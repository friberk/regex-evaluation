#! /usr/bin/env python3

import argparse
import gzip
from array import array
from typing import Union
import orjson as _json
import pickle


def collect_ids(in_path: str,
                       out_path: str,
                       id_field: str = "id",
                       allow_strings: bool = False) -> int:
    """
    Stream-read an NDJSON file (optionally .gz). Each line is a JSON object with an 'id' key.
    Collect IDs into memory, then dump them to out_path.

    Output format:
      - *.txt / *.csv / *.tsv (and *.gz variants): newline-delimited values
      - anything else: pickle (binary). For numeric ids, it's array('Q'); for strings, it's list[str].

    Params:
      - allow_strings: if True, accept string IDs; output will be list[str].
                       if False (default), coerce to unsigned integers (array('Q')).

    Returns:
      - Number of IDs collected.
    """
    # Open input (gzip or plain)
    is_gz = in_path.lower().endswith(".gz")
    opener = gzip.open if is_gz else open

    if allow_strings:
        ids: list[str] = []
        def _push(v): ids.append(v)
    else:
        ids = array("Q")
        def _push(v): ids.append(v)

    with opener(in_path, "rb") as f:
        for raw_line in f:
            if not raw_line.strip():
                continue
            try:
                obj =  _json.loads(raw_line)
            except Exception:
                continue  # skip malformed lines

            if not isinstance(obj, dict):
                continue
            v = obj.get(id_field)
            if v is None:
                continue

            if allow_strings:
                # Always store as string when allow_strings=True
                _push(str(v))
            else:
                # Store as unsigned 64-bit; coerce strings like "123" too
                try:
                    iv = int(v)
                    if iv < 0:
                        continue
                    _push(iv)
                except (ValueError, TypeError):
                    # Skip non-numeric IDs unless allow_strings=True
                    continue

    _dump_ids(ids, out_path)
    return len(ids)

def _dump_ids(ids: Union[array, list], out_path: str) -> None:
    lower = out_path.lower()

    # Text (one ID per line), optionally gzipped
    if lower.endswith((".txt", ".csv", ".tsv", ".txt.gz", ".csv.gz", ".tsv.gz")):
        text_gz = lower.endswith(".gz")
        opener = (lambda p, m: gzip.open(p, m)) if text_gz else open
        mode = "wt"
        with opener(out_path, mode, encoding="utf-8", newline="\n") as f:
            for v in ids:
                f.write(str(v))
                f.write("\n")
        return

    # Default: compact binary via pickle
    with open(out_path, "wb") as f:
        pickle.dump(ids, f, protocol=pickle.HIGHEST_PROTOCOL)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract regex-related posts IDs from StackOverflow Posts.xml dump')
    parser.add_argument('--regex-posts-file', '-f', help='Path to JSON file containing regex-related posts', required=True)
    parser.add_argument('--out-file', '-o', help='Where to dump IDs?', required=True)

    args = parser.parse_args()

    total = collect_ids(args.regex_posts_file, args.out_file)
    print(f"Wrote {total} IDs to {args.out_file}")
