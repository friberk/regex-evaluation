# regex_async.py

import asyncio
import datetime
import re
import time
from typing import Dict, List, Tuple, Optional
import argparse
import os
import traceback
import logging

import orjson
import zstandard as zstd
import regex as rx
rx.DEFAULT_VERSION = rx.VERSION1
from tqdm import tqdm

from openai import AsyncOpenAI, APIError, RateLimitError, APITimeoutError
from openai._types import NOT_GIVEN

from playhouse.sqlite_ext import SqliteExtDatabase, JSONField

from regex_generation.db.models import (
    LlmGenerationAttempt,
    LlmGenerationQuery,
    LlmGeneratedCandidate,
    LlmGenerationTask,
    db_proxy,
)

logger = logging.getLogger(__name__)

# -------- CLI / Config --------

def build_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Query LLMs for regex generation (async).")
    p.add_argument("--input-file", required=True, help="Path to input NDJSON with positive and negative strings")
    p.add_argument("--sqlite-db", required=True, help="Path to SQLite database to store results")
    p.add_argument("--prompt-file", required=True, help="Path to prompt file")
    p.add_argument("--model", default="gpt-5", help="OpenAI model")
    p.add_argument("--concurrency", type=int, default=4, help="Max concurrent API requests (global)")
    p.add_argument("--max-retries", type=int, default=5, help="LLM feedback/retry cycles (not HTTP retries)")
    p.add_argument("--max-tokens", type=int, default=256, help="Max tokens to generate")
    p.add_argument("--temperature", type=float, default=1.0, help="Temperature (unused if model forces it)")
    p.add_argument("--top-p", type=float, default=1.0, help="Top-p")
    p.add_argument("--seed", type=int, default=0, help="Seed for reproducibility")
    p.add_argument("--reasoning-effort", type=str, default=None, help="Reasoning effort (if supported by model)")
    p.add_argument("--verbosity", type=str, default=None, help="Verbosity (if supported by model)")
    p.add_argument("--no-of-candidates", type=int, default=3, help="Number of candidate regex solutions")
    p.add_argument("--base-url", type=str, default="https://api.openai.com/v1", help="Base URL for OpenAI API")
    p.add_argument("--regex-timeout", type=float, default=3.0, help="Timeout for regex matching (default: 3.0)")
    p.add_argument("--http-timeout", type=float, default=120.0, help="Per-request timeout seconds")
    p.add_argument("--log-level", type=str, default="INFO", help="Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL")
    p.add_argument("--log-file", type=str, default=None, help="Optional path to a log file")
    p.add_argument("--requery", action="store_true", help="If set, delete existing matching queries and attempts and re-run")
    p.add_argument("--experiment-id", type=str, default=None, help="Experiment ID for tracking queries")
    p.add_argument("--resume", action="store_true", help="If set, resume from the queries that set 'pending' status")
    return p.parse_args()

# -------- DB setup --------

def init_db(db_path: str) -> SqliteExtDatabase:
    db = SqliteExtDatabase(
        db_path,
        pragmas={
            "journal_mode": "wal",
            "busy_timeout": 10000,   # 10s to reduce 'database is locked' under concurrency
            "synchronous": 1,
        },
    )
    db_proxy.initialize(db)
    return db

def create_schema_if_needed():
    db = db_proxy.obj
    db.create_tables([LlmGenerationTask, LlmGenerationQuery, LlmGenerationAttempt, LlmGeneratedCandidate])

# -------- Logging --------

def setup_logging(level: str = "INFO", log_file: Optional[str] = None) -> None:
    numeric = getattr(logging, level.upper(), logging.INFO)
    handlers: List[logging.Handler] = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    logging.basicConfig(
        level=numeric,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handlers,
        force=True,
    )

# -------- Utilities --------

def to_blob(obj, level: int = 6) -> bytes:
    raw = orjson.dumps(obj)
    return zstd.ZstdCompressor(level=level).compress(raw)

def load_system_prompt(prompt_file: str) -> str:
    with open(prompt_file, "r", encoding="utf-8") as f:
        return f.read().strip()

def dump_request(d: dict) -> dict:
    # Keep 0/False/""/[]; only strip None and NOT_GIVEN
    return {k: v for k, v in d.items() if v is not None and v is not NOT_GIVEN}

def make_messages(system_prompt: str, positive_strings: List[str], negative_strings: List[str]) -> List[Dict[str, str]]:
    payload = {"positive_strings": positive_strings, "negative_strings": negative_strings}
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": orjson.dumps(payload).decode("utf-8")},
    ]

def append_to_messages(messages: List[Dict[str, str]], to_append: str) -> List[Dict[str, str]]:
    # If last message is a USER message, append as ASSISTANT; else append as USER.
    role = messages[-1]["role"]
    append_role = "assistant" if role == "user" else "user"
    messages.append({"role": append_role, "content": to_append})
    return messages

def make_response_format(no_of_candidates: int = 3, start_at_zero: bool = True, model_name: str = "gpt-5") -> dict:
    if no_of_candidates < 1:
        raise ValueError("no_of_candidates must be >= 1")

    if "qwen" in model_name.lower() or "deepseek" in model_name.lower() or "grok" in model_name.lower():
        return {"type": "json_object"}

    start = 0 if start_at_zero else 1
    end = start + no_of_candidates
    properties = {f"candidate_{i}": {"type": "string"} for i in range(start, end)}
    required = [f"candidate_{i}" for i in range(start, end)]
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "regex_generation",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "candidate_regex_solutions": {
                        "type": "object",
                        "properties": properties,
                        "required": required,
                        "additionalProperties": False,
                    }
                },
                "required": ["candidate_regex_solutions"],
                "additionalProperties": False,
            },
        },
    }

# -------- Core evaluation --------

def evaluate_regex_solutions(
    query: LlmGenerationQuery,
    attempt: LlmGenerationAttempt,
    regex_solutions: str,
    positive_strings: List[str],
    negative_strings: List[str],
    generation_time: float,
    regex_timeout: float = 3.0
) -> str:
    try:
        regex_solutions_dict = orjson.loads(regex_solutions)["candidate_regex_solutions"]
    except Exception as e:
        search_regex = r"```json\s*(.*?)\s*```"
        match = re.search(search_regex, regex_solutions, re.DOTALL)
        if match:
            try:
                regex_solutions_dict = orjson.loads(match.group(1))["candidate_regex_solutions"]
            except Exception as e1:
                return f"Your response format was incorrect. Please provide your response in the provided JSON format. Parsing error: {e1}"
        else:
            search_regex2 = r"(\{.*?\})"
            match2 = re.search(search_regex2, regex_solutions, re.DOTALL)
            if match2:
                try:
                    regex_solutions_dict = orjson.loads(match2.group(1))["candidate_regex_solutions"]
                except Exception as e2:
                    return f"Your response format was incorrect. Please provide your response in the provided JSON format. Parsing error: {e2}"
            else:
                return f"Your response format was incorrect. Please provide your response in the provided JSON format. Parsing error: {e}"

    issues = {}
    total = len(positive_strings) + len(negative_strings)

    for k, pattern in regex_solutions_dict.items():
        should_have_matched = []
        should_not_have_matched = []
        compat = True
        compat_error = None
        correct = 0

        try:
            rx.compile(pattern)
        except Exception as e:
            compat = False
            compat_error = str(e)

        if compat:
            for s in positive_strings:
                try:
                    if rx.fullmatch(pattern, s, timeout=regex_timeout):
                        correct += 1
                    else:
                        should_have_matched.append(s)
                except Exception as e:
                    should_have_matched.append(f"{s} (Error: {e})")

            for s in negative_strings:
                try:
                    if rx.fullmatch(pattern, s, timeout=regex_timeout):
                        should_not_have_matched.append(s)
                    else:
                        correct += 1
                except Exception as e:
                    should_not_have_matched.append(f"{s} (Error: {e})")

        accuracy = correct / max(1, total)
        LlmGeneratedCandidate.create(
            query=query, attempt=attempt, regex_pattern=pattern, accuracy=accuracy, generation_time=generation_time
        )

        if should_have_matched or should_not_have_matched or not compat:
            issues[k] = {
                "should_have_matched": should_have_matched,
                "should_not_have_matched": should_not_have_matched,
                "compat": compat,
                "compat_error": compat_error,
            }

    if not issues:
        return "CORRECT"

    feedback = "You need to revise your " + ", ".join(issues.keys()) + f" solution{'s' if len(issues)>1 else ''}. Here is the detailed feedback:\n"
    for k, v in issues.items():
        if v["compat"]:
            feedback += f"\n- Your {k} regex {regex_solutions_dict[k]}:\n"
            if v["should_have_matched"]:
                feedback += f"  - Should have matched these positive strings: {', '.join(v['should_have_matched'])}\n"
            if v["should_not_have_matched"]:
                feedback += f"  - Should not have matched these negative strings: {', '.join(v['should_not_have_matched'])}\n"
        else:
            feedback += f"\n- Your {k} regex {regex_solutions_dict[k]} is not compilable by the Python `regex` module. Error: {v['compat_error']}\n"

    non_mentioned = set(regex_solutions_dict.keys()) - set(issues.keys())
    if non_mentioned:
        feedback += f"\nKeep your {', '.join(non_mentioned)} solution{'s' if len(non_mentioned)>1 else ''} as they are since they are correct and working as expected."
    return feedback

# -------- Async OpenAI call --------

class OpenAIInvoker:
    def __init__(self, client: AsyncOpenAI, api_semaphore: asyncio.Semaphore, http_timeout: float):
        self.client = client
        self.api_semaphore = api_semaphore
        self.http_timeout = http_timeout

    def build_request_payload(self, model: str, messages: List[Dict[str, str]], temperature: Optional[float], top_p: Optional[float], reasoning_effort: Optional[str], verbosity: Optional[str], seed: Optional[int], response_format: dict, timeout: Optional[float]) -> dict:
        request_payload = dump_request(
            {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "top_p": top_p,
                "reasoning_effort": reasoning_effort,
                "verbosity": verbosity,
                "seed": seed,
                "response_format": response_format,
                "timeout": timeout,
            }
        )
        return request_payload

    async def ask_openai(
        self,
        *,
        request_payload: dict,
    ):
        # Bound the number of in-flight API calls
        async with self.api_semaphore:
            t0 = time.perf_counter()
            try:
                # Let SDK handle its own transient retries; also set timeout per request
                response = await self.client.chat.completions.create(**request_payload)
                elapsed = time.perf_counter() - t0
                response_received_at = datetime.datetime.utcnow()
                return response, response_received_at, elapsed
            except Exception as e:
                # attach elapsed so caller can persist/log it
                setattr(e, "api_roundtrip_seconds", time.perf_counter() - t0)
                setattr(e, "response_received_at", datetime.datetime.utcnow())
                raise

# -------- Query orchestration (async) --------

async def async_query_llm(
    invoker: OpenAIInvoker,
    system_prompt: str,
    task: LlmGenerationTask,
    args: argparse.Namespace,
    db_lock: asyncio.Lock,
) -> bool:
    # Ensure task is persisted
    if task.get_id() is None or not task._pk:
        async with db_lock:
            task.save(force_insert=True)
    logger.debug("Starting query orchestration for task_id=%s", task.get_id())

    query_parameters = {
        "model": args.model,
        "temperature": args.temperature,
        "top_p": args.top_p,
        "reasoning_effort": args.reasoning_effort,
        "verbosity": args.verbosity,
        "seed": args.seed,
        "no_of_candidates": args.no_of_candidates,
        "timeout": args.http_timeout,
    }
    if args.experiment_id:
        query_parameters["experiment_id"] = args.experiment_id

    query = LlmGenerationQuery(
        task=task,
        query_parameters=query_parameters,
        system_prompt=system_prompt,
        status="pending",
    )

    # Duplicate check now also includes prompt hash
    queries = LlmGenerationQuery.select().where(
        (LlmGenerationQuery.task == query.task)
        & (LlmGenerationQuery.query_parameters == query.query_parameters)
        & (LlmGenerationQuery.system_prompt == query.system_prompt)
    )
    if args.requery:
        # If requery is requested, remove existing queries (and their attempts) before proceeding
        async with db_lock:
            existing_count = queries.count()
            attempts = LlmGenerationAttempt.select().where(
                LlmGenerationAttempt.query.in_(queries)
            )
            attempts_count = attempts.count()
            if existing_count:
                # Delete attempts tied to these queries first (be explicit regardless of FK cascade settings)
                LlmGenerationAttempt.delete().where(
                    LlmGenerationAttempt.query.in_(queries)
                ).execute()
                # Delete the queries themselves
                LlmGenerationQuery.delete().where(
                    (LlmGenerationQuery.task == query.task)
                    & (LlmGenerationQuery.query_parameters == query.query_parameters)
                    & (LlmGenerationQuery.system_prompt == query.system_prompt)
                ).execute()
                logger.info(
                    "Requery enabled: deleted %s old queries and %s attempts for task_id=%s",
                    existing_count,
                    attempts_count,
                    task.get_id(),
                )
            # return True
    elif args.resume:
        # Get the queries that are in 'pending' status
        pending_ids = LlmGenerationQuery.select(LlmGenerationQuery.id).where((LlmGenerationQuery.status == "pending") & (LlmGenerationQuery.task == task)
        & (LlmGenerationQuery.query_parameters == query.query_parameters)
        & (LlmGenerationQuery.system_prompt == query.system_prompt)
        )

        # How many we're about to resume
        resumed_count = pending_ids.count()

        if resumed_count == 0:
            logger.info("No queries to resume for task_id=%s", task.get_id())
            return True

        if resumed_count:
            # Delete attempts tied to those queries
            (LlmGenerationAttempt
                .delete()
                .where(LlmGenerationAttempt.query.in_(pending_ids))
                .execute())

            # Delete the queries themselves
            (LlmGenerationQuery
                .delete()
                .where(LlmGenerationQuery.id.in_(pending_ids))
                .execute())

            logger.info("Resumed %s queries for task_id=%s",
                        resumed_count, task.get_id())

    elif queries.exists():
        logger.info("Duplicate query detected for task_id=%s; skipping creation", task.get_id())
        return True

    async with db_lock:
        query.save(force_insert=True)

    response_format = make_response_format(args.no_of_candidates, start_at_zero=False, model_name=args.model)
    messages = make_messages(system_prompt, task.positive_examples, task.negative_examples)

    call_attempt = 0
    ok = False

    while call_attempt <= args.max_retries:
        try:
            # Create attempt row
            async with db_lock:
                attempt, created = LlmGenerationAttempt.get_or_create(
                    query=query,
                    attempt_number=call_attempt,
                    defaults=dict(
                        status="pending",
                        request_payload=None,
                        response_payload=None,
                        error_message=None,
                        response_received_at=None,
                        created_at=datetime.datetime.utcnow(),
                    ),
                )

            # Adjust seed for diversity across attempts
            effective_seed = (args.seed + call_attempt) if args.seed is not None else None
            logger.debug(
                "Attempt %s for task_id=%s (seed=%s)", call_attempt, task.get_id(), effective_seed
            )

            request_payload = invoker.build_request_payload(args.model, messages, args.temperature, args.top_p, args.reasoning_effort, args.verbosity, effective_seed, response_format, args.http_timeout)
            response_payload, response_received_at, generation_seconds = await invoker.ask_openai(
                request_payload=request_payload,
            )

            # Persist attempt
            rp = getattr(response_payload, "model_dump", None)
            response_as_dict = rp() if callable(rp) else dict(response_payload)

            async with db_lock:
                attempt.request_payload = request_payload
                attempt.response_payload = response_as_dict
                attempt.response_received_at = response_received_at
                attempt.save()

            regex_solutions = response_payload.choices[0].message.content
            feedback = evaluate_regex_solutions(
                query, attempt, regex_solutions, task.positive_examples, task.negative_examples, generation_seconds, args.regex_timeout
            )

            if feedback == "CORRECT":
                async with db_lock:
                    attempt.status = "success"
                    attempt.save()
                    query.status = "success"
                    query.save()
                logger.info(
                    "Task_id=%s succeeded on attempt=%s with generation_time=%.3fs",
                    task.get_id(),
                    call_attempt,
                    generation_seconds,
                )
                ok = True
                break
            else:
                async with db_lock:
                    attempt.status = "not_satisfied"
                    attempt.save()
                logger.debug("Task_id=%s attempt=%s not satisfied; providing feedback and retrying", task.get_id(), call_attempt)
                messages = append_to_messages(messages, regex_solutions)
                messages = append_to_messages(messages, feedback)
                call_attempt += 1

        except (RateLimitError, APITimeoutError) as e:
            # Backoff on rate/timeout, keep the attempt open as 'error'
            async with db_lock:
                attempt.response_received_at = getattr(e, "response_received_at", datetime.datetime.utcnow())
                attempt.request_payload = request_payload
                attempt.status = "timeout" if ("timeout" in str(e) or "time out" in str(e)) else "error"
                attempt.error_message = str(e)
                attempt.save()
            logger.warning("Task_id=%s attempt=%s encountered rate/timeout error: %s", task.get_id(), call_attempt, e)
            await asyncio.sleep(min(2 ** call_attempt, 30))  # exponential backoff with cap
            call_attempt += 1

        except APIError as e:
            # Non-retryable or 4xx/5xx unexpected
            async with db_lock:
                attempt.response_received_at = getattr(e, "response_received_at", datetime.datetime.utcnow())
                attempt.request_payload = request_payload
                attempt.status = "timeout" if ("timeout" in str(e) or "time out" in str(e)) else "error"
                attempt.error_message = str(e)
                attempt.save()
            logger.error("Task_id=%s attempt=%s APIError: %s", task.get_id(), call_attempt, e)
            call_attempt += 1

        except Exception as e:
            logger.exception("Unhandled exception for task_id=%s attempt=%s", task.get_id(), call_attempt)
            # async with db_lock:
            #     attempt.response_received_at = getattr(e, "response_received_at", datetime.datetime.utcnow())
            #     attempt.request_payload = request_payload
            #     attempt.status = "timeout" if ("timeout" in str(e) or "time out" in str(e)) else "error"
            #     attempt.error_message = str(e)
            #     attempt.save()
            logger.error("Task_id=%s attempt=%s Exception: %s", task.get_id(), call_attempt, e)
            # call_attempt += 1

    if not ok:
        async with db_lock:
            query.status = "retry_exceeded"
            query.save()
    return ok

# -------- NDJSON processing with task fan-out --------

async def process_ndjson_file_async(system_prompt: str, args: argparse.Namespace) -> None:
    # One async client for all calls; you can also use aiohttp backend for larger fanout.
    async with AsyncOpenAI(base_url=args.base_url) as client:
        api_semaphore = asyncio.Semaphore(args.concurrency)
        invoker = OpenAIInvoker(client, api_semaphore, http_timeout=args.http_timeout)
        db_lock = asyncio.Lock()

        # Count total lines for progress reporting
        try:
            with open(args.input_file, "rb") as fcount:
                total_tasks = sum(1 for _ in fcount)
        except Exception:
            total_tasks = None

        logger.info(
            "Preparing to process input file: %s (concurrency=%s, retries=%s)",
            args.input_file,
            args.concurrency,
            args.max_retries,
        )

        tasks: List[asyncio.Task] = []
        with open(args.input_file, "r", encoding="utf-8") as f:
            with tqdm(total=total_tasks, desc="Preparing tasks", dynamic_ncols=True) as prep_bar:
                for line in f:
                    data = orjson.loads(line)
                    positives = [s.get("subject") for s in data.get("positive_strings", [])]
                    negatives = [s.get("subject") for s in data.get("negative_strings", [])]
                    ground_truth = data.get("regex", None)

                    # Create/get Task row synchronously (guarded)
                    async with db_lock:
                        task_row, _ = LlmGenerationTask.get_or_create(
                            ground_truth=ground_truth,
                            positive_examples=positives,
                            negative_examples=negatives,
                        )

                    # Start the async query immediately, concurrency bounded by semaphore inside
                    t = asyncio.create_task(
                        async_query_llm(invoker, system_prompt, task_row, args, db_lock)
                    )
                    tasks.append(t)
                    prep_bar.update(1)

        # Run all queries concurrently (API concurrency bounded by semaphore)
        completed = 0
        total = len(tasks)
        logger.info("Dispatching %s LLM queries", total)
        with tqdm(total=total, desc="LLM queries", dynamic_ncols=True) as pbar:
            for fut in asyncio.as_completed(tasks):
                try:
                    await fut
                except Exception:
                    # Individual task exceptions were already logged inside async_query_llm
                    pass
                finally:
                    completed += 1
                    pbar.update(1)

# -------- Entrypoint --------

if __name__ == "__main__":
    args = build_args()

    setup_logging(args.log_level, args.log_file)

    if "localhost" in args.base_url:
        os.environ["OPENAI_API_KEY"] = "not-needed"

    system_prompt = load_system_prompt(args.prompt_file)
    init_db(args.sqlite_db)
    create_schema_if_needed()
    asyncio.run(process_ndjson_file_async(system_prompt, args))
