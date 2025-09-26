# Analysis — Figures and Targets

This package contains scripts that read the unified SQLite database and reproduce the figures and summary statistics reported in the paper.

## Structure
- `analysis_targets.py` — maps human‑readable labels to `experiment_id` values used in plots (e.g., `PATTERN_LENGTH_TARGETS`, `AUTOMATON_SIZE_TARGETS`). Update these to match your runs.
- `plot/*.py` — plotting scripts (box plots, line charts) for each metric and ablations.
- `plot/pdfs/*.pdf` — the figures produced by the scripts.
  - Special note: `plot/pdfs/llm_success_at_k_plot.pdf` shows the full accuracy results (i.e., their capability to solve the regex composition tasks at 1, 2, and 3 attempts) for each LLM listed in the paper. We selected GPT-5, gpt-oss-120b, gpt-oss-20b, based on their performance in that analysis.

## Using a results database
- You can point `--db-path` to any experiments DB you produced, or use the bundled results DB at `data/candidate_regexes/candidate_regexes.sqlite3` (full paper set).

## Requirements
- Python 3.10–3.11.
- Matplotlib + SciencePlots; Linux Libertine font (optional). If unavailable, plots still render with fallback fonts.

## Usage
All scripts accept `--db-path` pointing to your experiments SQLite file. Example commands:

- Average accuracy per task:
```
python -m analysis.plot.plot_average_accuracy --db-path runs/llm.sqlite3
```

- Pattern length (candidates vs. ground truth):
```
python -m analysis.plot.plot_pattern_length --db-path runs/llm.sqlite3
```

- Distinct features used:
```
python -m analysis.plot.plot_distinct_features --db-path runs/llm.sqlite3
```

- Syntactic similarity (AST distance):
```
python -m analysis.plot.plot_syntactic_similarity --db-path runs/llm.sqlite3
```

- Semantic similarity (if computed):
```
python -m analysis.plot.plot_semantic_similarity --db-path runs/llm.sqlite3
```

- Automaton size and generation time / candidate count:
```
python -m analysis.plot.plot_automaton_size --db-path runs/llm.sqlite3
python -m analysis.plot.plot_generation_time --db-path runs/llm.sqlite3
```

- Success vs. test suite size:
```
python -m analysis.plot.plot_test_suite_size_vs_accuracy --db-path runs/llm.sqlite3
```

- RbE success and synthesizer success (ablations):
```
python -m analysis.plot.plot_rbe_success --db-path runs/rbe.sqlite3
python -m analysis.plot.plot_synthesizer_success --db-path runs/synth.sqlite3
```

Scripts save figures (PNG/PDF) to the current working directory and print status to stdout.

## Notes
- The scripts query by `experiment_id` via `analysis_targets.py`; ensure your generation runs set matching `--experiment-id` values (see `regex_generation/*` READMEs).
- SQLite JSON1 is required (bundled in modern Python). DBs are opened read‑only; WAL mode is supported.
- If fonts are missing, ignore warnings; visuals should still match the reported figures.
