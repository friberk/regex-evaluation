# Reuse‑by‑Example (RbE) — High‑Throughput Search

This package searches a large corpus of real‑world regexes (SQLite) for candidates that satisfy a task specified by positive and negative strings. It updates the unified SQLite schema with tasks, queries, and candidates.

## Inputs
- Tasks NDJSON (one per line): `{ "regex": null|"^…$", "positive_strings": [{"subject":"…"}], "negative_strings": [{"subject":"…"}] }`
- Reuse corpus (SQLite): see `data/regexreusedb/regex_reuse_database.sqlite3` and its README.

## Run
```
python -m regex_generation.reuse_by_example.query_rbe \
  --input-file data/regexcompbench/reg_comp_bench.ndjson \
  --rbe-db data/regexreusedb/regex_reuse_database.sqlite3 \
  --sqlite-db runs/rbe.sqlite3 \
  --include-source all \
  --targeted-pos-accuracy 1.0 --targeted-neg-accuracy 1.0 \
  --num-partitions 4 --workers-per-partition 9 \
  --regex-matching-timeout 0.01 --collection-timeout 300 \
  --experiment-id EXP_RBE_ALL
```
Useful flags:
- `--include-source` one of `all`, `internet`, `oss` (filters the corpus by source).
- `--limit` limit number of candidates collected per task (optional).
- `--regex-matching-timeout` per‑match timeout in seconds.
- `--max-timeouts-per-regex` and `--max-wall-per-regex` skip pathological candidates.
- Parallelism: `--num-partitions * --workers-per-partition` processes.
- `--start-method` (`fork`/`spawn`/`forkserver`) and `--maxtasks-per-child` for stability on your OS.
- `--drop-tables` to clear RbE result tables in the results DB before running.
- `--no-progress` to disable TQDM bars.

## How it works
- Loads tasks from NDJSON; creates/gets an `rbe_generation_tasks` row for each unique (positives, negatives, ground_truth).
- For each task, scans the reuse DB and evaluates each candidate pattern with bounded time per match:
  - Accept if it meets `--targeted-pos-accuracy` and `--targeted-neg-accuracy` over provided strings.
  - Computes per‑candidate accuracy and wall time; writes rows to `rbe_generated_candidates`.
- Writes a `rbe_generation_queries` row with `query_parameters` (include_source, thresholds, timeouts, experiment_id) and status (`success`, `solution_not_found`, or `error`).

## Schema
- Tasks: `rbe_generation_tasks` (positive/negative examples and optional ground truth).
- Queries: `rbe_generation_queries` (parameters + status).
- Candidates: `rbe_generated_candidates` (regex_pattern, accuracy, generation_time).

## Tips
- Start strict (`1.0/1.0`) for exact satisfaction, then relax (e.g., `--targeted-neg-accuracy 0.95`) if needed.
- Keep `--regex-matching-timeout` small (e.g., 10–20ms) to avoid catastrophic patterns; tune `--max-*` fail‑safes accordingly.
- Tag runs with `--experiment-id` to group queries in analysis.
