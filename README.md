# Regex Evaluation – Replication Package

This repository is the replication package for the paper:
“Is Reuse All You Need? A Systematic Comparison of Regular Expression Composition Strategies.”
It evaluates three families of regex composition: reuse-by-example (RbE) over a mined corpus (RegexReuseDB),
large language models (LLMs), and classical synthesizers. The package includes:

- Data artifacts and sample benchmarks (RegexCompBench: 55,448 tasks; RegexReuseDB: 901,516 unique regexes)
- Candidate generators (LLM, RbE, synthesizers) writing to a unified SQLite schema
- Metric calculators (pattern length, distinct features, syntactic similarity, semantic similarity, automaton size, strictness)
- Analysis scripts to reproduce figures reported in the manuscript

Key finding (see paper): RbE and strong LLMs achieve near‑perfect accuracy on RegexCompBench; RbE offers greater solution variety across non‑functional dimensions; classical synthesis (e.g., RFixer) underperforms more often.

## 1 Environment setup
Requirements: Python 3.10 or 3.11 (macOS/Linux).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```
Notes:
- Some plots use SciencePlots and the Linux Libertine font. If “Linux Libertine O” is missing, matplotlib falls back (plots still render).
- `metrics/semantic_similarity/egret_ext.*.so` is provided for common Linux CPython 3.10/3.11. On macOS, other metrics work; semantic similarity requires EGRET (Linux).

## 2 Project structure
- `regex_generation/` – candidate generation
  - `llms/` – async OpenAI‑compatible pipeline (stores attempts, candidates, accuracy)
  - `reuse_by_example/` – multiprocessing RbE search over a large regex DB
  - `synthesizers/` – Ray runners for RFixer, FOREST, RegexPlus
  - `db/models.py` – Peewee models and shared SQLite schema
- `metrics/` – calculators and helpers (`calculate_metrics.py`, `syntactic_similarity/`, `semantic_similarity/`, `strictness_score/`)
- `analysis/` – analysis targets and plotting scripts
- `data/` – input datasets and mined corpora

## 3 Data inputs
Pipelines consume NDJSON, one task per line:
```json
{
  "test_suite_id": "optional-id",
  "regex": "optional ground truth or null",
  "positive_strings": [{"subject": "..."}],
  "negative_strings": [{"subject": "..."}]
}
```
Provided datasets:
- `data/regexcompbench/*.ndjson` – real‑world benchmark tasks
- `data/regexreusedb/regex_reuse_database.sqlite3` – mined regex corpus used by RbE

## 4 Unified SQLite database
All scripts read/write a single SQLite file you choose via `--sqlite-db`/`--db-path`.
Schema lives in `regex_generation/db/models.py` and is created on demand:
- Tasks: `llm_generation_tasks`, `rbe_generation_tasks`, `synthesizer_generation_tasks`
- Queries/Attempts per approach; Candidates: `*_generated_candidates`
- Metrics: `candidate_regex_metrics`, `ground_truth_metrics`, `strictness_scores`
Tip: keep runs isolated (e.g., `runs/exp1.sqlite3`).

## 5 Reproducing candidate generation
5.1 LLM (OpenAI‑compatible API)
```bash
export OPENAI_API_KEY=...   # unless using a local-compatible base_url
python -m regex_generation.llms.query_llms \
  --input-file data/regexcompbench/regexcompbench.ndjson \
  --sqlite-db runs/llm.sqlite3 \
  --prompt-file regex_generation/llms/prompts/prompt_two_candidates.md \
  --model gpt-5 \
  --no-of-candidates 3 \
  --experiment-id EXP_LLM_GPT5
```
Useful flags: `--base-url`, `--concurrency`, `--requery`, `--resume`, `--http-timeout`.

5.2 Reuse‑by‑Example (RbE)
```bash
python -m regex_generation.reuse_by_example.query_rbe \
  --input-file data/regexcompbench/regexcompbench.ndjson \
  --rbe-db data/regexreusedb/regex_reuse_database.sqlite3 \
  --sqlite-db runs/rbe.sqlite3 \
  --include-source all \
  --targeted-pos-accuracy 1.0 --targeted-neg-accuracy 1.0 \
  --experiment-id EXP_RBE_ALL
```
Tuning: `--num-partitions`, `--workers-per-partition`, `--regex-matching-timeout`, `--max-wall-per-regex`.

5.3 Synthesizers (RFixer/FOREST/RegexPlus)
```bash
python -m regex_generation.synthesizers.query_synthesizers \
  --input-file data/regexcompbench/regexcompbench.ndjson \
  --sqlite-db runs/synth.sqlite3 \
  --synthesizer RFixer \
  --path-to-synthesizer /path/to/rfixer.jar \
  --experiment-id EXP_SYN_RFIXER
```
Swap `--synthesizer` and `--path-to-synthesizer` for FOREST/RegexPlus.

## 6 Computing metrics
Ground truth (per task):
```bash
python -m metrics.calculate_metrics \
  --db-path runs/llm.sqlite3 --type llm --experiment-id EXP_LLM_GPT5 \
  --metric pattern_length --ground-truth
python -m metrics.calculate_metrics \
  --db-path runs/llm.sqlite3 --type llm --experiment-id EXP_LLM_GPT5 \
  --metric distinct_features --ground-truth
```
Candidates:
```bash
python -m metrics.calculate_metrics --db-path runs/llm.sqlite3 --type llm \
  --experiment-id EXP_LLM_GPT5 --metric pattern_length
python -m metrics.calculate_metrics --db-path runs/llm.sqlite3 --type llm \
  --experiment-id EXP_LLM_GPT5 --metric distinct_features
python -m metrics.calculate_metrics --db-path runs/llm.sqlite3 --type llm \
  --experiment-id EXP_LLM_GPT5 --metric syntactic_similarity --timeout-seconds 5
python -m metrics.calculate_metrics --db-path runs/llm.sqlite3 --type llm \
  --experiment-id EXP_LLM_GPT5 --metric automaton_size --timeout-seconds 5
```
Semantic similarity (Linux EGRET extension required):
```bash
python -m metrics.calculate_metrics --db-path runs/llm.sqlite3 --type llm \
  --experiment-id EXP_LLM_GPT5 --metric semantic_similarity --timeout-seconds 10
```

## 7 Plotting (analysis)
Targets used in figures are defined in `analysis/analysis_targets.py` (e.g., `PATTERN_LENGTH_TARGETS`). Example:
```bash
python -m analysis.plot.plot_pattern_length --db-path runs/llm.sqlite3
```
Scripts save figures (e.g., PNG/PDF) into the working directory.

## 8 Repro tips
- Set `--experiment-id` consistently; analysis groups by it across approaches.
- WAL mode and table creation are enabled in scripts; runs are idempotent under unique constraints.
- Long jobs (LLM calls, Ray, EGRET) can be resumed with `--resume` (LLMs) or re‑run safely.
- Prefer separate DBs per approach: `runs/llm.sqlite3`, `runs/rbe.sqlite3`, `runs/synth.sqlite3`.
