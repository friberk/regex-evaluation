# Candidate Regexes — Results Database (Full Paper Set)

This folder contains the complete SQLite database (`candidate_regexes.sqlite3`) of generated candidates and computed metrics used in the paper. It aggregates results across all strategies evaluated: reuse‑by‑example (RbE), large language models (LLMs), and formal synthesizers.

## Data Model (what is a task, query, attempt, candidate?)
The unified schema is defined in `regex_generation/db/models.py` and created by the pipelines.

- Task: a regex composition task defined by `ground_truth` (optional) and example sets `positive_examples` and `negative_examples`.
  - Tables: `rbe_generation_tasks`, `llm_generation_tasks`, `synthesizer_generation_tasks`.
- Query: one concrete run/configuration of a Task for a given strategy. Captures `query_parameters` (e.g., `model`, `synthesizer`, `experiment_id`, timeouts) and, for LLMs, the `system_prompt`.
  - Tables: `rbe_generation_queries`, `llm_generation_queries`, `synthesizer_generation_queries`.
- Attempt (LLM only): a single API call/feedback round within a Query. Stores request/response payloads, status, and timestamps.
  - Table: `llm_generation_attempts`.
- Candidate: a produced `regex_pattern` for a Query, with per‑candidate `accuracy` and `generation_time` (seconds). One Query may have multiple Candidates.
  - Tables: `rbe_generated_candidates`, `llm_generated_candidates`, `synthesizer_generated_candidates`.
- Metrics: derived measures stored per candidate and per task.
  - Candidate metrics: `candidate_regex_metrics` (pattern length, distinct features, syntactic/semantic similarity, automaton size, strictness).
  - Ground‑truth metrics: `ground_truth_metrics` (per task).
  - Strictness runs: `strictness_scores` (for RbE/LLM candidates).

Notes:
- Uniqueness constraints prevent duplicate rows for the same logical entity (see model indexes in `models.py`).
- `query_parameters` is JSON; most analyses filter by `$.experiment_id`.

## Exploring the database (SQLite JSON1)
Open and list tables:
```
.open data/candidate_regexes/candidate_regexes.sqlite3
.tables
```
Counts per strategy:
```
SELECT 'llm' kind, COUNT(*) FROM llm_generated_candidates
UNION ALL SELECT 'rbe', COUNT(*) FROM rbe_generated_candidates
UNION ALL SELECT 'synth', COUNT(*) FROM synthesizer_generated_candidates;
```
Filter by experiment (LLM example):
```
SELECT COUNT(*)
FROM llm_generated_candidates c
JOIN llm_generation_queries q ON q.id = c.query_id
WHERE json_extract(q.query_parameters, '$.experiment_id') = 'EXP_LLM_GPT5';
```
Best candidate per task (LLM):
```
SELECT t.id AS task_id, MAX(c.accuracy) AS best_acc
FROM llm_generation_tasks t
JOIN llm_generation_queries q ON q.task_id = t.id
LEFT JOIN llm_generated_candidates c ON c.query_id = q.id
GROUP BY t.id;
```
Join metrics (automaton size and syntactic similarity if computed):
```
SELECT c.regex_pattern,
       json_extract(m.automaton_size, '$.automaton_size') AS automaton_size,
       json_extract(m.syntactic_similarity, '$.normalized_ast_edit_distance') AS norm_ast_dist
FROM llm_generated_candidates c
JOIN candidate_regex_metrics m ON m.llm_candidate_id = c.id
ORDER BY automaton_size DESC
LIMIT 20;
```

## Recomputing metrics or adding new ones
Use `metrics/calculate_metrics.py` to (re)populate metrics; it upserts only missing fields.
Examples:
```
python -m metrics.calculate_metrics \
  --db-path data/candidate_regexes/candidate_regexes.sqlite3 \
  --type llm --experiment-id EXP_LLM_GPT5 --metric pattern_length

python -m metrics.calculate_metrics \
  --db-path data/candidate_regexes/candidate_regexes.sqlite3 \
  --type rbe --experiment-id EXP_RBE_ALL --metric automaton_size --timeout-seconds 5
```
Semantic similarity requires the bundled EGRET extension on Linux (see `metrics/semantic_similarity/`).

## Tips
- Use separate DBs for new runs; treat this file as the canonical paper dataset.
- Queries over `query_parameters` require SQLite JSON1 (`json_extract`).
