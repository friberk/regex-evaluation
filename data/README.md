# data/ — Datasets and Corpora

This directory holds the datasets and corpora used in the paper. In paper terms: the reuse corpus (RegexReuseDB) and the benchmark of composition tasks (RegexCompBench).

## Layout
- `regexcompbench/` — Benchmark tasks (NDJSON):
  - `regexcompbench.ndjson` (full), `regexcompbench_evaluation.ndjson`, `regexcompbench_ablation.ndjson` (sampled from the full dataset).
  - Helpers: `build_regexcompbench.py`, `sample_regexcompbench.py`.
- `regexreusedb/` — Reuse corpus (SQLite):
  - `regex_reuse_database.sqlite3` and `schema.sql` (DDL reference).
  - Consumed by RbE: `regex_generation/reuse_by_example/query_rbe.py`.
- `internet_regexes/` — Provenance from web sources (NDJSON):
  - `regexlib/*.ndjson`, `stackoverflow/*.ndjson` (filtered and spam/false positives removed).
- `candidate_regexes/` — Contains all generated candidates with their respective metrics.
- `util/` — Source extractors (Stack Overflow, RegExLib); used to build `internet_regexes/`.

## File formats
- NDJSON (one JSON object per line) with fields:
  - `regex` (optional ground truth), `positive_strings`/`negative_strings` arrays with `{ "subject": "..." }`.
- SQLite (Peewee/Playhouse): see `regex_generation/db/models.py` for the unified results schema; see `regexreusedb/schema.sql` for the reuse corpus DDL.