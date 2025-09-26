# Internet Regexes — Outputs from Web Extractors

This directory holds the regex corpora produced by the utilities in `data/util/` after processing RegExLib and Stack Overflow. These NDJSON files are intermediate artifacts used to build/augment the reuse corpus (`data/regexreusedb/regex_reuse_database.sqlite3`).

## Contents
- `regexlib/`
  - `regexlib-regexesFiltered.ndjson` — RegExLib entries kept after scraping/post‑processing (spam filtering).
  - `regexlib-regexesSpam.ndjson` — Entries flagged as spam.
- `stackoverflow/`
  - `stackoverflow-regexesFromPostsFiltered.ndjson` — Regexes extracted from answers/posts (after FP filtering).
  - `stackoverflow-regexesFromPostsDiscarded.ndjson` — Discarded or pre‑extraction patterns from posts.
  - `stackoverflow-regexesFromCommentsFiltered.ndjson` — Regexes extracted from comments (after FP filtering).
  - `stackoverflow-regexesFromCommentsDiscarded.ndjson` — Discarded or pre‑extraction patterns from comments.

## Record formats
- RegExLib rows (from CSV→NDJSON conversion):
  - Keys: `id, title, expression, description, matches, non_matches, author_source, rating, comment_count, category`
  - `matches` and `non_matches` are arrays of strings taken from RegExLib examples.
  - Example:
    {"id": 1234, "title": "Email", "expression": "^…$", "description": "…", "matches": ["a@b.com"], "non_matches": ["x"], "author_source": "…", "rating": 4, "comment_count": 0, "category": "Email"}

- Stack Overflow rows (from extractors):
  - Keys: `patterns` (array of strings), `type` ("StackOverflowPostRegexSource" or "StackOverflowCommentRegexSource"), `uri`, `uriAliases`.
  - After false‑positive filtering, `patterns` contains only valid or extracted regex patterns.
  - Example:
    {"patterns": ["^cat|dog$"], "type": "StackOverflowPostRegexSource", "uri": "https://www.stackoverflow.com/a/123", "uriAliases": ["https://stackoverflow.com/a/123"]}

## How these are produced
- RegExLib: see `data/util/regexlib_regex_extractor/` for scraping, category enrichment, post‑processing (Cloudflare email decode), CSV→NDJSON conversion, and spam filtering with the OpenAI batch pipeline.
- Stack Overflow: see `data/util/stackoverflow_regex_extractor/` for obtaining XML dumps, finding regex‑tagged questions/answers, extracting patterns from code/inline backticks, and filtering false positives with the OpenAI batch pipeline.

## Usage notes
- These NDJSON files are not required to run LLM/synth experiments; they are inputs for constructing the reuse corpus used by RbE.
- Heuristics: RegExLib is targeted by spammers who advertise their services; with the help of the OpenAI batch pipeline, we are able to filter out the spam.
- Heuristics: Stack Overflow extraction focuses on single‑line code/backticked segments; multi‑line snippets are ignored to reduce noise. Post‑filters remove non‑regex strings and extract embedded regexes.

## Rebuilding or extending
- To regenerate these files, follow the step‑by‑step commands in `data/util/README.md` (Stack Overflow XML downloads are not included in this repository).
- To ingest into a database, adapt scripts in `data/regexreusedb/` or your own ETL to map sources and patterns to tables.
