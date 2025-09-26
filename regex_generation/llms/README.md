# LLM Pipeline — Async Regex Generation

This package queries LLMs to generate candidate regexes for each task (positive/negative strings), evaluates them online, and stores all attempts, candidates, and metrics in the unified SQLite schema.

## Input and environment
- Input NDJSON (one task per line):
  ``
  {"regex": null, "positive_strings": [{"subject": "aaa"}], "negative_strings": [{"subject": "ab"}]}
  ``
- Python 3.10–3.11 recommended.
- Authentication: set `OPENAI_API_KEY` unless using a local proxy via `--base-url` (if `localhost` appears in the base URL, the script sets a dummy key).

## Prompts
- System prompts live under `regex_generation/llms/prompts/*.md`.
- Provide one with `--prompt-file`. The user content is a JSON object of `{positive_strings, negative_strings}`.

## Run
```
python regex_generation/llms/query_llms.py \
  --input-file data/regexcompbench/reg_comp_bench.ndjson \
  --sqlite-db runs/llm.sqlite3 \
  --prompt-file regex_generation/llms/prompts/prompt_two_candidates.md \
  --model gpt-5 \
  --no-of-candidates 3 \
  --concurrency 4 \
  --experiment-id EXP_LLM_GPT5
```
Useful flags:
- `--base-url` OpenAI‑compatible endpoint (default `https://api.openai.com/v1`).
- `--max-retries` feedback iterations per query (not HTTP retries).
- `--http-timeout` per request; `--regex-timeout` per match check.
- `--requery` delete prior rows for same task+params+prompt; `--resume` re‑run only pending queries.
- `--log-level` and optional `--log-file` for diagnostics.

## Response format required from the model
- The pipeline requests JSON via response_format. Expected keys are `candidate_regex_solutions.candidate_1..candidate_N` (1‑indexed).
- If the model returns fenced code or a raw object, the loader attempts to recover JSON; otherwise the attempt is marked unsatisfied and feedback is provided.

## How it works
- Builds messages: system = prompt file; user = JSON with positive/negative strings.
- Calls Chat Completions asynchronously with a bounded semaphore (`--concurrency`).
- Parses and evaluates candidates with Python `regex` and `--regex-timeout`:
  - Computes per‑candidate accuracy on the provided strings.
  - If all candidates are correct, marks query `success`.
  - Else constructs granular feedback (missed positives/negatives or compile errors) and retries up to `--max-retries`.

## Schema and persistence
- Tasks: `llm_generation_tasks` (positive/negative examples, optional ground truth).
- Queries: `llm_generation_queries` (params + system_prompt, status).
- Attempts: `llm_generation_attempts` (request/response payloads, status, timestamps).
- Candidates: `llm_generated_candidates` (regex_pattern, accuracy, generation_time).
- Pipelines enable WAL and create tables on demand. Use `--experiment-id` to tag `query_parameters` for grouping in analysis.
