import ast
import sys
import orjson
from typing import Any

def parse_listish(value):
    # Already a list/tuple? normalize to list.
    if isinstance(value, (list, tuple)):
        return list(value)
    # String that looks like a Python literal list? Try to parse safely.
    if isinstance(value, str) and value.startswith('[') and value.endswith(']'):
        try:
            out = ast.literal_eval(value)  # safe for Python literals
            if isinstance(out, (list, tuple)):
                # Strip stray leading/trailing double quotes in items like '"foo'
                return [str(x).strip('"') for x in out]
        except Exception:
            print(f"Failed to parse listish: {value}")
            input("Press Enter to continue...")
    return value

def normalize_record(rec: Any) -> Any:
    """If the record is a dict, coerce 'matches'/'non_matches' into arrays."""
    if not isinstance(rec, dict):
        return rec
    rec = dict(rec)  # shallow copy
    for k in ("matches", "non_matches"):
        if k in rec:
            rec[k] = parse_listish(rec[k])
    return rec

def sort_ndjson_from_path(in_path: str, out_path: str) -> None:
    """
    Streams input NDJSON -> output NDJSON, fixing list-like fields.
    Keeps files open during iteration to avoid 'readline of closed file'.
    """
    records = []
    with open(in_path, "rb") as src, open(out_path, "ab") as dst:
        for i, line in enumerate(src, 1):
            if not line.strip():
                continue
            try:
                rec = orjson.loads(line)
                records.append(rec)
            except Exception as e:
                print(f"Warning: line {i} is not valid JSON ({e}); skipping.", file=sys.stderr)
                continue

    records.sort(key=lambda x: x["id"])
    with open(out_path, "ab") as dst:
        for rec in records:
            rec = normalize_record(rec)
            out = orjson.dumps(rec) + b"\n"
            dst.write(out)
            dst.flush()

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, help="Path to input NDJSON file")
    p.add_argument("--output", required=True, help="Path to output NDJSON file")
    args = p.parse_args()

    sort_ndjson_from_path(args.input, args.output)