#!/usr/bin/env python3
"""
Spam-filter a NDJSON using OpenAI, fast — and write results incrementally.

Example:
  python spam_filter.py --input-file input.ndjson --output-file filtered.ndjson \
    --spam-output-file spam.ndjson --concurrency 32

Notes:
  - Requires OPENAI_API_KEY in your environment.
"""

import argparse
import asyncio
from functools import partial
import os
import sys
from typing import Dict, List
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential
from fast_ndjson_processor import FastNDJSONProcessor, FastNDJSONWriter
import orjson
from openai import AsyncOpenAI

SYSTEM_PROMPT = (
    "You are a moderator on RegExLib.com, which is a community-driven online library of regexes (with example strings) that developers can search, share, and reuse.\n\n"
    "TASK\n"
    "Decide if a single submission is SPAM or OK.\n\n"
    "INPUT\n"
    "You will receive one TASK JSON OBJECT with these keys:\n"
    "- title: string\n"
    "- description: string\n"
    "- author: string\n"
    "- pattern: string\n"
    "- matches: list of strings\n"
    "- non_matches: list of strings\n\n"
    "RETURN\n"
    "Return exactly one of the following strings, by itself on a single line:\n"
    "SPAM\n"
    "OK\n"
    "Use uppercase ASCII letters only. No punctuation, no spaces, no explanation, no extra tokens.\n\n"
    "DECISION RULES\n"
    "Label as SPAM only if the description clearly contains:\n"
    "- Unsolicited ads, scams, SEO junk, clickbait, phishing, crypto 'invest' pitches, adult/NSFW promotions, gambling/dating spam, or other irrelevant promotions unrelated to the regex pattern.\n"
    "\n"
    "Label as OK if:\n"
    "- The description explains what the regex pattern matches\n"
    "- The description contains technical explanations about regex functionality\n"
    "- The description includes examples or use cases for the regex\n"
    "- The description is relevant to programming or data validation\n"
    "- When in doubt, prefer labeling as OK\n"
    "\n"
    "RETURN\n"
    "Only the single word: SPAM or OK."
)

def build_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Filter spammy rows from a NDJSON using OpenAI (incremental writes).")
    p.add_argument("--input-file", required=True, help="Path to input NDJSON")
    p.add_argument("--output-file", required=True, help="Path to write filtered (non-spam) NDJSON")
    p.add_argument("--spam-output-file", default=None, help="Optional path to write only spam rows")
    p.add_argument("--model", default="gpt-5-nano", help="OpenAI model (default: gpt-5-nano)")
    p.add_argument("--n-workers", type=int, default=os.cpu_count(), help="Number of workers")
    p.add_argument("--concurrency-per-worker", type=int, default=128, help="Max concurrent requests per worker")
    p.add_argument("--truncate", type=int, default=4000,
                   help="Max description chars to send per row (to limit tokens)")
    p.add_argument("--max-retries", type=int, default=5, help="Retries on transient errors")
    p.add_argument("--max-tokens", type=int, default=3, help="Max tokens to generate")
    p.add_argument("--temperature", type=float, default=0, help="Temperature for OpenAI")
    p.add_argument("--seed", type=int, default=42, help="Seed for random number generator")
    p.add_argument("--reasoning-effort", type=str, default="low", help="Reasoning effort for OpenAI")
    p.add_argument("--verbosity", type=str, default="low", help="Verbosity level")
    return p.parse_args()

def make_messages(record: dict, truncate: int = 4000) -> List[Dict[str, str]]:
    description = record.get("description") or ""
    truncated_description = (description[:truncate] + "...") if len(description) > truncate else description
    payload = {
        "title": record.get("title", ""),
        "description": truncated_description,
        "author": record.get("author_source", ""),
        "pattern": record.get("expression", ""),
        "matches": record.get("matches", []),  # Limit matches to 10 examples
        "non_matches": record.get("non_matches", []),  # Limit non-matches to 10 examples
    }

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": orjson.dumps(payload).decode("utf-8")}
    ]

def is_spam_label(label: str) -> bool:
    return "SPAM" in label

async def ask_openai(client: AsyncOpenAI, messages: List[Dict[str, str]], model: str, max_retries: int, max_tokens: int, temperature: float, reasoning_effort: str, verbosity: str, seed: int, sem: asyncio.Semaphore) -> str:
    async with sem:
        async for attempt in AsyncRetrying(stop=stop_after_attempt(max_retries), wait=wait_exponential(min=1, max=30)):
            with attempt:
                resp = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=1 if model == "gpt-5-nano" else temperature, # gpt-5-nano doesn't support temperature
                    # max_completion_tokens=max_tokens,
                    reasoning_effort=reasoning_effort,
                    verbosity=verbosity,
                    seed=seed,
                )
                result = (resp.choices[0].message.content or "").strip().upper()
            if not attempt.retry_state.outcome.failed:
                attempt.retry_state.set_result(result)
        return result

async def classify_and_write_async(record: dict, args: argparse.Namespace, client: AsyncOpenAI, sem: asyncio.Semaphore):
    """Async version of classify and write for a single record."""
    messages = make_messages(record, truncate=args.truncate)
    label = await ask_openai(
        client, messages,
        args.model, args.max_retries, args.max_tokens,
        args.temperature, args.reasoning_effort,
        args.verbosity, args.seed, sem
    )

    if is_spam_label(label):
        if args.spam_output_file:
            with open(args.spam_output_file, "a") as f:
                f.write(orjson.dumps(record).decode("utf-8") + "\n")
    else:
        with open(args.output_file, "a") as f:
            f.write(orjson.dumps(record).decode("utf-8") + "\n")

def process_chunk_sync(records: List[dict], args_dict: dict) -> None:
    """
    Synchronous wrapper that runs async processing inside each process.
    This function will be called by each multiprocessing worker.
    """
    # Reconstruct args from dict
    args = argparse.Namespace(**args_dict)

    # Use asyncio.run which handles event loop creation and cleanup properly
    try:
        asyncio.run(process_records(records, args))
    except Exception as e:
        print(f"Error processing chunk: {e}", file=sys.stderr)

async def process_records(records: List[dict], args: argparse.Namespace):
    """Process records with proper resource management for the async client."""
    # Create semaphore for this process
    sem = asyncio.Semaphore(args.concurrency_per_worker)

    # Create a single client for all records
    client = AsyncOpenAI()
    try:
        # Create tasks with a shared client
        tasks = [classify_and_write_async(record, args, client, sem) for record in records]

        # Wait for all tasks to complete
        if tasks:
            await asyncio.gather(*tasks)
    finally:
        # Ensure client is always closed
        await client.close()

if __name__ == "__main__":
    args = build_args()

    # Count lines for chunk calculation
    with open(args.input_file, "rb") as f:
        line_count = sum(1 for _ in f)

    # Convert args to dict for multiprocessing (can't pickle Namespace directly)
    args_dict = vars(args)

    processor = FastNDJSONProcessor(n_workers=args.n_workers, show_progress=True)

    # Use a lambda to pass args_dict to the sync function
    chunk_handler = partial(process_chunk_sync, args_dict=args_dict)

    processor.process_file_chunks(args.input_file, chunk_handler, return_results=False)
