# Data Utilities — Internet Corpus Builders

This directory contains extraction and cleaning utilities used to build the internet portions of the reuse corpus (RegexReuseDB) from Stack Overflow and RegExLib. Outputs are NDJSON files under `data/internet_regexes/` and feed the reuse SQLite at `data/regexreusedb/regex_reuse_database.sqlite3`.

## Stack Overflow Extractor (`stackoverflow_regex_extractor/`)
Purpose: parse Stack Overflow data dumps to collect regex‑related posts/comments and extract candidate regex patterns from inline/backticked code.

### Get the Stack Overflow XML dumps (we do not provide these)
- Posts table (required):
  - Download: `https://archive.org/download/stackexchange/stackoverflow.com-Posts.7z`
  - Size after extract: ~70–80 GB
- Comments table (optional, for comment patterns):
  - Download: `https://archive.org/download/stackexchange/stackoverflow.com-Comments.7z`
- Example commands:
  ```bash
  mkdir -p data/util/stackoverflow_regex_extractor/raw-data
  cd data/util/stackoverflow_regex_extractor/raw-data
  wget --no-clobber https://archive.org/download/stackexchange/stackoverflow.com-Posts.7z
  wget --no-clobber https://archive.org/download/stackexchange/stackoverflow.com-Comments.7z  # optional
  7z e stackoverflow.com-Posts.7z
  7z e stackoverflow.com-Comments.7z  # optional
  cd -
  ```

### Extract regex posts and patterns
- Posts tagged “regex” (questions + answers) → NDJSON posts file:
  ```bash
  python -m data.util.stackoverflow_regex_extractor.find-regex-posts \
    --all-posts-file data/util/stackoverflow_regex_extractor/raw-data/Posts.xml \
    --out-file data/util/stackoverflow_regex_extractor/data/stackoverflow-regexPosts.json
  ```
- Extract patterns from post code blocks (single‑line) → NDJSON sources:
  ```bash
  python -m data.util.stackoverflow_regex_extractor.extract-regexes-from-posts \
    --regex-posts data/util/stackoverflow_regex_extractor/data/stackoverflow-regexPosts.json \
    --out-file data/internet_regexes/stackoverflow/stackoverflow-regexesFromPostsFiltered.ndjson
  ```
- Optional: extract patterns from comments on those posts:
  ```bash
  # Collect post IDs
  python -m data.util.stackoverflow_regex_extractor.extract-ids-from-regex-posts \
    --regex-posts-file data/util/stackoverflow_regex_extractor/data/stackoverflow-regexPosts.json \
    --out-file data/util/stackoverflow_regex_extractor/data/stackoverflow-regexPostIds.txt

  # Parse comments and extract patterns from backticked code
  python -m data.util.stackoverflow_regex_extractor.extract-regexes-from-comments \
    --comments-file data/util/stackoverflow_regex_extractor/raw-data/Comments.xml \
    --regex-post-ids data/util/stackoverflow_regex_extractor/data/stackoverflow-regexPostIds.txt \
    --out-file data/internet_regexes/stackoverflow/stackoverflow-regexesFromCommentsFiltered.ndjson
  ```

### Filter false positives (clean non‑regex or embedded code)
Use the OpenAI‑batch‑based filter to classify each extracted string as VALID, INVALID, or PARTIALLY VALID and (optionally) extract embedded regexes. Two phases: submit batches (query) and, after completion, produce filtered/discarded files (filter).

- Submit batches and record batch IDs:
  ```bash
  export OPENAI_API_KEY=...  # required
  python -m data.util.stackoverflow_regex_extractor.filter-stackoverflow-fp \
    --input-file data/internet_regexes/stackoverflow/stackoverflow-regexesFromPostsFiltered.ndjson \
    --batch-id-file runs/so_batches.txt \
    --custom-id-prefix so-post \
    --mode query
  # Repeat for comments if desired (change input-file/custom-id-prefix)
  ```
  Monitor batch status in your OpenAI account. Wait until all batch IDs written to `runs/so_batches.txt` have an output file.

- Build lookup table from completed batches and write filtered outputs:
  ```bash
  python -m data.util.stackoverflow_regex_extractor.filter-stackoverflow-fp \
    --input-file data/internet_regexes/stackoverflow/stackoverflow-regexesFromPostsFiltered.ndjson \
    --batch-id-file runs/so_batches.txt \
    --output-file data/internet_regexes/stackoverflow/stackoverflow-regexesFromPostsFiltered.ndjson \
    --discarded-output-file data/internet_regexes/stackoverflow/stackoverflow-regexesFromPostsDiscarded.ndjson \
    --custom-id-prefix so-post \
    --mode filter
  ```
Notes:
- The script classifies each `patterns[]` entry and, for PARTIALLY VALID, can emit an `extracted_regex`. The filtered NDJSON retains only final regex strings.
- Requires network access and may incur API costs.

## RegExLib Extractor (`regexlib_regex_extractor/`)
Purpose: scrape RegExLib entries (title, pattern, description, example matches/non‑matches, author, rating), fix protected emails, assign category, convert to NDJSON, and optionally spam‑filter.

Typical pipeline:
- Scrape and post‑process to CSV (creates headers if needed):
  ```bash
  python -m data.util.regexlib_regex_extractor.regexlib_regex_extractor \
    --out-file data/internet_regexes/regexlib/regexlib.csv
  ```
  Optional scraping function inside the script: `scrape_regexlib(start=1, end=35500)`; `fetch_categories()` tags entries; `post_process_csv` normalizes fields and decodes Cloudflare‑protected emails.
- Convert CSV → NDJSON:
  ```bash
  python -m data.util.regexlib_regex_extractor.convert_regexlib_csv_to_ndjson \
    --csv-file data/internet_regexes/regexlib/regexlib.csv \
    --out-file data/internet_regexes/regexlib/regexlib-regexesFiltered.ndjson
  ```
- Optional: filter spam with LLM moderation:
  ```bash
  python -m data.util.regexlib_regex_extractor.regexlib_filter_spam \
    --input-file data/internet_regexes/regexlib/regexlib-regexesFiltered.ndjson \
    --output-file data/internet_regexes/regexlib/regexlib-regexesFiltered.ndjson \
    --spam-output-file data/internet_regexes/regexlib/regexlib-regexesSpam.ndjson
  ```

## Outputs and integration
- Stack Overflow outputs: `data/internet_regexes/stackoverflow/*.ndjson`
- RegExLib outputs: `data/internet_regexes/regexlib/*.ndjson`
- These NDJSON files can be ingested into the reuse DB or used as standalone sources for analysis.

## Requirements & tips
- Environment: Python 3.10/3.11; install `requirements.txt` plus `lxml`, `beautifulsoup4`, `pandas`, `requests`, `tqdm`, `py7zr` (or system `7z`).
- OpenAI filtering: set `OPENAI_API_KEY`; consider smaller `--n-batches`/`--concurrency` to manage quota.
