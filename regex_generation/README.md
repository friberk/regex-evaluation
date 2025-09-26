# Regex Generation — Pipelines and Schema

This package implements the three candidate-generation strategies evaluated in the paper and a shared SQLite schema (via Peewee) used by all pipelines.

## Subpackages
- `llms/` — Async OpenAI‑compatible pipeline. Stores tasks, queries, attempts, and candidates; evaluates accuracy online.
- `reuse_by_example/` — High‑throughput RbE search over a mined regex corpus (SQLite). Multiprocessing with timeouts.
- `synthesizers/` — Ray‑based runners for RFixer, FOREST, and RegexPlus; computes per‑candidate accuracy.
- `db/models.py` — Unified schema (tasks → queries/attempts → candidates; plus metric tables).

## Input format (NDJSON)
One task per line:
```
{"regex": "optional GT or null", "positive_strings": [{"subject": "…"}], "negative_strings": [{"subject": "…"}]}
```

## Run pipelines
- LLM candidates (requires OPENAI_API_KEY or `--base-url`):
```
python -m regex_generation.llms.query_llms \
  --input-file data/regexcompbench/reg_comp_bench.ndjson \
  --sqlite-db runs/llm.sqlite3 \
  --prompt-file regex_generation/llms/prompts/prompt_two_candidates.md \
  --model gpt-5 --no-of-candidates 3 --experiment-id EXP_LLM_GPT5
```
Useful: `--concurrency`, `--requery`, `--resume`, `--http-timeout`, `--regex-timeout`.

- Reuse‑by‑Example (RbE) over the corpus:
```
python -m regex_generation.reuse_by_example.query_rbe \
  --input-file data/regexcompbench/reg_comp_bench.ndjson \
  --rbe-db data/regexreusedb/regex_reuse_database.sqlite3 \
  --sqlite-db runs/rbe.sqlite3 \
  --include-source all --targeted-pos-accuracy 1.0 --targeted-neg-accuracy 1.0 \
  --experiment-id EXP_RBE_ALL
```
Tuning: `--num-partitions`, `--workers-per-partition`, `--regex-matching-timeout`.

- Synthesizers (RFixer/FOREST/RegexPlus):
```
python -m regex_generation.synthesizers.query_synthesizers \
  --input-file data/regexcompbench/reg_comp_bench.ndjson \
  --sqlite-db runs/synth.sqlite3 \
  --synthesizer RFixer --path-to-synthesizer /path/to/rfixer.jar \
  --experiment-id EXP_SYN_RFIXER
```

## Schema & experiment IDs
- Tables: `*_generation_tasks`, `*_generation_queries`, `llm_generation_attempts`, `*_generated_candidates`.
- Metrics tables: `candidate_regex_metrics`, `ground_truth_metrics`, `strictness_scores`.
- Pipelines enable WAL and create tables on demand. Use `query_parameters.experiment_id` to scope analyses (see `analysis/analysis_targets.py`).
