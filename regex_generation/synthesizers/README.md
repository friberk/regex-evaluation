# Synthesizers — Ray‑Based Candidate Generation

This package runs classical regex synthesizers on each task and writes candidates into the unified SQLite schema. Supported backends: RFixer, FOREST, and RegexPlus.

## Inputs and prerequisites
- Tasks NDJSON (one per line): `{ "regex": null|"^…$", "positive_strings": [{"subject":"…"}], "negative_strings": [{"subject":"…"}] }`.
- RFixer: Java runtime and the synthesizer JAR (`--path-to-synthesizer /path/to/rfixer.jar`).
- FOREST: Python script entry (e.g., `regex_generation/synthesizers/FOREST/forest.py`).
- RegexPlus: bundled in this repo; no external binary required.

## Run
```
python -m regex_generation.synthesizers.query_synthesizers \
  --input-file data/regexcompbench/reg_comp_bench.ndjson \
  --sqlite-db runs/synth.sqlite3 \
  --synthesizer RFixer \
  --path-to-synthesizer /path/to/rfixer.jar \
  --experiment-id EXP_SYN_RFIXER
```
Swap `--synthesizer` and `--path-to-synthesizer` for `FOREST` and `RegexPlus` accordingly.

Common flags:
- `--num-workers` number of Ray workers (defaults to available CPUs).
- `--timeout` per‑task synthesizer timeout (seconds).
- `--no-progress` disable progress bars.

## How it works
- Loads tasks from NDJSON and ensures a `synthesizer_generation_tasks` row exists.
- Creates a `synthesizer_generation_queries` row with `query_parameters` (synthesizer, experiment_id, timeout).
- Uses Ray to fan out tasks; each worker invokes the chosen synthesizer:
  - RFixer: writes temp input file with positives/negatives, runs the JAR, parses `#sol#...#sol#`.
  - FOREST: writes temp input file and runs the Python entry (`forest.py`) to obtain a candidate.
  - RegexPlus: calls the Python entrypoint and collects a candidate list.
- For each candidate: computes accuracy using Python `regex` with a 3s per‑match timeout, then inserts into `synthesizer_generated_candidates` with `generation_time`.
- Updates query `status` based on synthesizer result (`success`, `solution_not_found`, `error`, `timeout`); persists any `error_message`.

## Schema
- Tasks: `synthesizer_generation_tasks` (positive/negative examples, optional ground truth).
- Queries: `synthesizer_generation_queries` (parameters + status + error_message).
- Candidates: `synthesizer_generated_candidates` (regex_pattern, accuracy, generation_time).

## Tips
- Ensure synthesizer paths are executable and their runtime deps are installed (Java for RFixer, Python env for FOREST).
- Use a conservative `--timeout` to cap pathological runs; keep DB on SSD for faster centralized updates.
- Tag runs with `--experiment-id` so analysis scripts can group results.
- For clusters, configure Ray per your environment (the script uses `ray.init()` with packaged modules).
