# regexreusedb — Reuse Corpus (RbE Source Database)

This directory provides the SQLite corpus used by the reuse‑by‑example (RbE) pipeline. It aggregates regexes and (where available) their test suites mined from open‑source projects and internet sources, as described in the paper’s RegexReuseDB.

## Contents
- `regex_reuse_database.sqlite3` — the full reuse corpus consumed by `regex_generation/reuse_by_example/query_rbe.py` via `--rbe-db`.
- `schema.sql` — schema DDL reference for the corpus.

## Schema overview (key tables)
- `regex_entity(id, pattern, flags, static, dynamic)` — unique regex patterns (pattern+flags).
- `project_spec(id, name, repo, license, language, downloads)` — source projects/posts.
  - Internet sources use names like `RegExLib`, `Stack Overflow Posts`, `Stack Overflow Comments`.
- `regex_source_usage(id, line_no, source_file, commit_hash, project_id, regex_id)` — where a regex was seen.
- `test_suite(id, project_id, regex_id, …coverage…)` — per‑regex test suites where available.
- `test_suite_string(id, test_suite_id, subject, func, full_match, partial_match, first_sub_match_start, first_sub_match_end)` — strings for test suites.
- `test_suite_result(test_suite_id, regex_id, project_id, full_match_result, partial_match_result, …distances…, …coverage…)` — evaluation results of candidate vs. test suite.

Indexes are created on common join/filter keys (`regex_entity.id`, `pattern`, `test_suite.regex_id`, etc.).

## Using with the RbE pipeline
Run RbE search against this corpus:
```bash
python -m regex_generation.reuse_by_example.query_rbe \
  --input-file data/regexcompbench/regexcompbench.ndjson \
  --rbe-db data/regexreusedb/regex_reuse_database.sqlite3 \
  --sqlite-db runs/rbe.sqlite3 \
  --include-source all \
  --targeted-pos-accuracy 1.0 --targeted-neg-accuracy 1.0 \
  --experiment-id EXP_RBE_ALL
```
`--include-source` can be `all`, `internet` (RegExLib + Stack Overflow), or `oss` (open‑source projects).

## Example SQL (SQLite)
List sources and counts of unique regexes seen:
```sql
SELECT p.name, COUNT(DISTINCT r.id) AS regex_count
FROM regex_entity r
JOIN regex_source_usage u ON u.regex_id = r.id
JOIN project_spec p ON p.id = u.project_id
GROUP BY p.name
ORDER BY regex_count DESC;
```
Fetch a regex and its test suite strings:
```sql
SELECT r.id, r.pattern, s.subject, s.full_match, s.partial_match
FROM regex_entity r
JOIN test_suite t ON t.regex_id = r.id
JOIN test_suite_string s ON s.test_suite_id = t.id
WHERE r.id = 12345;
```
