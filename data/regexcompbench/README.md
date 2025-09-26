# RegexCompBench — Composition Tasks (NDJSON)

This folder contains the benchmark used in the paper for evaluating regex composition methods. Each row is a composition task consisting of a ground‑truth regex and an associated test suite (positive/negative example strings).

## Files
- `regexcompbench.ndjson` — full benchmark exported from the reuse corpus.
- `regexcompbench_evaluation.ndjson` — evaluation set (used for figures; ~95% conf., ±5% MoE in the paper).
- `regexcompbench_ablation.ndjson` — ablation/tuning set (~90% conf., ±10% MoE).
- Helpers: `build_regexcompbench.py` (export from SQLite), `sample_regexcompbench.py` (preprocess + stratified sample).

## Row format (NDJSON)
```
{
  "test_suite_id": 12345,
  "regex": "^…$",
  "project": {"id": 1, "name": "…", "repo": "…"},
  "positive_strings": [{
    "id": 24141, "subject": "…", "func": "RegExp#test",
    "full_match": 1, "partial_match": 0,
    "first_sub_match_start": 0, "first_sub_match_end": 3
  }],
  "negative_strings": [ { … } ]
}
```
Interpretation:
- Positives: strings that the ground truth matched (full or partial; see Notes).
- Negatives: strings not matched (no full/partial match). Subject is the raw string.

## Build and sample
- Export from the reuse DB (JSON1 path preferred):
  ```bash
  python -m data.regexcompbench.build_regexcompbench \
    --db data/regexreusedb/regex_reuse_database.sqlite3 \
    --output data/regexcompbench/regexcompbench.ndjson
  ```
- Create a stratified sample for experiments (trims/cleans rows first):
  ```bash
  python -m data.regexcompbench.sample_regexcompbench \
    --input data/regexcompbench/regexcompbench.ndjson \
    --output data/regexcompbench/regexcompbench_evaluation.ndjson \
    --confidence 0.95 --margin 0.05 --bins-test 4 --bins-pos 4 --seed 42 --emit-metadata
  ```

## Notes (preprocessing and strata)
- Trimming rules (in sampler):
  - Keep only full‑match positives; convert partial matches to full matches by slicing the matched span; drop rows without ≥1 positive and ≥1 negative; discard non‑compilable or too‑long regexes; de‑duplicate by subject.
  - Optional constraints: `--ensure-ascii`, `--min-subject-length`.
- Stratification (sampler): buckets on source (`RegExLib` vs non‑RegExLib), test_count (quantile bins), and pos_rate (quantile bins). Total `n` computed via Cochran with FPC; per‑stratum `n_h` via Neyman allocation.

## Use in pipelines
All pipelines accept this NDJSON directly via `--input-file`:
- LLM: `regex_generation/llms/query_llms.py`
- RbE: `regex_generation/reuse_by_example/query_rbe.py`
- Synthesizers: `regex_generation/synthesizers/query_synthesizers.py`
