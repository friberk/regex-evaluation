# Metrics — Candidate and Ground-Truth Evaluation

This package computes functional and non‑functional metrics for regex candidates and ground truths, writing results into the unified SQLite schema used across the artifact.

## What it measures
- pattern_length (scalar) — length of the regex pattern.
- distinct_features (scalar) — fast heuristic count of distinct regex features (see `count_distinct_features.py`).
- automaton_size (JSON) — approximate automaton size for a pattern (used for complexity analyses).
- syntactic_similarity (JSON, needs GT) — AST edit distance to ground truth (see `syntactic_similarity/`).
- semantic_similarity (JSON, needs GT, Linux only) — EGRET‑based semantic similarity (see `semantic_similarity/`).

Output tables: `candidate_regex_metrics` (per‑candidate) and `ground_truth_metrics` (per task). Fields are updated idempotently; existing values are not recomputed.

## CLI
Use `metrics/calculate_metrics.py` to populate metrics.

Common flags:
- `--db-path` path to the experiments DB.
- `--type` one of `llm`, `rbe`, `synth` (source of candidates).
- `--experiment-id` substring matched in `query_parameters.experiment_id` to scope queries.
- `--metric` one of: `pattern_length`, `distinct_features`, `automaton_size`, `syntactic_similarity`, `semantic_similarity`.
- `--timeout-seconds` per‑item timeout for expensive metrics (e.g., 5–10s).
- `--num-workers` process count (defaults to CPUs‑1).
- `--batch-size` DB write batch size (default 2000).
- `--ground-truth` switch to operate on tasks and upsert into `ground_truth_metrics`.

## Examples
- Candidates (LLM run):
```
python -m metrics.calculate_metrics \
  --db-path runs/llm.sqlite3 --type llm --experiment-id EXP_LLM_GPT5 \
  --metric pattern_length

python -m metrics.calculate_metrics \
  --db-path runs/llm.sqlite3 --type llm --experiment-id EXP_LLM_GPT5 \
  --metric syntactic_similarity --timeout-seconds 5
```
- Ground truth metrics:
```
python -m metrics.calculate_metrics \
  --db-path runs/llm.sqlite3 --type llm --experiment-id EXP_LLM_GPT5 \
  --metric pattern_length --ground-truth
```

## Dependencies & notes
- Semantic similarity requires the EGRET extension (`semantic_similarity/egret_ext.*.so`) on Linux CPython 3.10/3.11. On macOS, skip this metric.
- Syntactic similarity uses an AST‑based distance (see `syntactic_similarity/ast.py`, `distance.py`).
- The tool enables SQLite WAL and batches updates. It filters by `experiment_id` via JSON1; ensure your SQLite has JSON1 enabled (bundled by default in modern Python).

## Tips
- Run scalar metrics first; they are fastest.
- Use specific `--experiment-id` values (see `analysis/analysis_targets.py`).
- For large runs, keep DB on SSD and increase `--num-workers` conservatively to avoid CPU contention.
