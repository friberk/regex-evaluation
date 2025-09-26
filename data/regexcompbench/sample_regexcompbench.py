#!/usr/bin/env python3
"""
Read NDJSON of test suites, preprocess, then draw a stratified sample with
95% confidence and 5% margin of error (configurable).

Preprocessing (per row):
1) Keep only *full-matches* positives: positive_strings where full_match == 1 AND partial_match != 1.
2) Require at least one positive and one negative string after trimming; otherwise drop the row.
3) Drop rows whose regex is not compilable by Python's re module.

Stratification (best practices):
- project_name ∈ { "RegExLib", "non-RegExLib" }.
  * If the row has a single "project" object, use its name.
  * If the row has "projects" (array), treat it as "RegExLib" if ANY project has that name.
- test_count: total strings (positives + negatives) AFTER trimming, binned by *quantiles* (default 4 bins).
- pos_rate: positives / (positives + negatives) AFTER trimming, binned by *quantiles* (default 4 bins).

Sampling:
- Target total sample size uses Cochran's formula for proportions with finite population correction (FPC):
    n0 = (Z^2 * p*(1-p)) / e^2, with p=0.5 (worst case), Z for given confidence (default 1.96 for 95%).
    n = n0 / (1 + (n0 - 1)/N)   (FPC), clipped to [1, N].
- Within-stratum allocation uses Neyman allocation:
    n_h ∝ N_h * S_h, where S_h is the sample std dev of pos_rate in the stratum
    (fallback S_h = sqrt(p_h*(1-p_h)) if needed).
- Guarantees at least 1 sample from any non-empty stratum (if overall n allows).
- Random sampling is without replacement and reproducible via --seed.

I/O:
- Input NDJSON rows like your examples (supports either "project" or "projects").
- Output NDJSON includes the *trimmed* row. If you pass --emit-metadata, we also attach:
  {"_meta": {"project_bucket": ..., "test_count": ..., "pos_rate": ..., "test_count_bin": "...", "pos_rate_bin": "..."}}

Usage:
  python sample_suites.py --input preprocessed.ndjson --output sample.ndjson
Options:
  --confidence 0.95   --margin 0.05   --bins-test 4   --bins-pos 4   --seed 42   --emit-metadata
"""

import argparse
import json
import math
import random
import regex as rx
rx.DEFAULT_VERSION = rx.VERSION1
import sys
from collections import defaultdict
from statistics import pstdev

# -------------------------- Helpers --------------------------

def z_for_confidence(conf: float) -> float:
    # Common z-scores; fallback to 1.96
    table = {
        0.80: 1.2816, 0.85: 1.4395, 0.90: 1.6449,
        0.95: 1.96,   0.98: 2.3263, 0.99: 2.5758,
        0.995: 2.807, 0.999: 3.2905
    }
    # snap to known value if close
    for k, v in table.items():
        if abs(conf - k) < 1e-6:
            return v
    return table.get(round(conf, 3), 1.96)


def cochran_sample_size(N: int, confidence: float = 0.95, margin: float = 0.05, p: float = 0.5) -> int:
    """
    Cochran's formula for proportions with finite population correction (FPC).
    """
    z = z_for_confidence(confidence)
    e = margin
    n0 = (z * z * p * (1.0 - p)) / (e * e)
    # FPC for finite population
    n = n0 / (1.0 + (n0 - 1.0) / max(N, 1))
    n = int(math.ceil(n))
    return max(1, min(n, N))


def safe_compile(pattern: str) -> bool:
    try:
        rx.compile(pattern)
        return True
    except Exception as e:
        return False


def is_regexlib_name(name: str) -> bool:
    if name is None:
        return False
    return name.strip().lower() == "regexlib"


def project_bucket(row: dict) -> str:
    # Accept either "project" (single) or "projects" (array)
    if "project" in row and isinstance(row["project"], dict):
        return "RegExLib" if is_regexlib_name(row["project"].get("name")) else "non-RegExLib"
    if "projects" in row and isinstance(row["projects"], list):
        for p in row["projects"]:
            if is_regexlib_name((p or {}).get("name")):
                return "RegExLib"
        return "non-RegExLib"
    # If missing, consider non-RegExLib
    return "non-RegExLib"

from collections import defaultdict

def _canon_subjects(lst):
    # Canonicalize by SUBJECT TEXT only (after trim), order-independent, multiplicity preserved.
    # Change this if you want stricter equality.
    return tuple(sorted((s or {}).get("subject", "") for s in (lst or [])))

def dedupe_by_strings(rows):
    """
    Collapse rows that have the same sets of positive/negative subjects.
    Keeps one random representative per duplicate group (seeded by --seed).
    """
    groups = defaultdict(list)
    for r in rows:
        key = (_canon_subjects(r.get("positive_strings")),
               _canon_subjects(r.get("negative_strings")))
        groups[key].append(r)
    return [random.choice(v) for v in groups.values()]


def _sample_unique_by_subject(strings_list):
    """
    From a list of string objects, group by subject and sample one object per subject.
    Assumes global random seed is set for reproducibility.
    """
    by_subject = defaultdict(list)
    for item in (strings_list or []):
        subj = (item or {}).get("subject", "")
        by_subject[subj].append(item)
    return [random.choice(items) for items in by_subject.values()]


def trim_row(row: dict, min_subject_length: int, ensure_ascii: bool) -> dict | None:
    """
    - Keep only full-matches positives (full_match == 1 and partial_match != 1)
    - Require ≥1 positive and ≥1 negative
    - Regex must compile
    - Ensure ASCII-only subjects if --ensure-ascii is set
    - Ensure minimum subject length if --min-subject-length is set
    - Deduplicate by subject within positives and negatives by sampling one per subject
    Returns trimmed row or None if it should be dropped.
    """
    regex = row.get("regex", "")

    if ensure_ascii:
        if not regex.isascii():
            return None

    if not isinstance(regex, str) or not safe_compile(regex):
        return None

    if len(regex) > 1000:
        return None # Regex is too long

    pos = row.get("positive_strings") or []
    neg = row.get("negative_strings") or []

    # Keep only FULL-match positives (full_match==1)
    # pos_trim = [
    #     s for s in pos
    #     if (s or {}).get("full_match", 0) == 1
    # ]

    pos_trim = []

    for s in pos:
        if (s or {}).get("full_match", 0) == 1:
            if ensure_ascii and not s["subject"].isascii():
                continue

            if len(s["subject"]) >= min_subject_length:
                pos_trim.append(s)


        elif (s or {}).get("partial_match", 0) == 1:
            # "id":24141,"subject":"-123.45","func":"RegExp#test","full_match":0,"partial_match":0,"first_sub_match_start":-1,"first_sub_match_end":-1}
            new_subject = s["subject"][s["first_sub_match_start"]:s["first_sub_match_end"]]

            if ensure_ascii and not new_subject.isascii():
                continue

            if len(new_subject) < min_subject_length:
                continue

            d = {
                "id": s["id"],
                # Get the substring of the subject that was matched
                "subject": new_subject,
                "func": s["func"],
                "full_match": 1,
                "partial_match": s["partial_match"],
                "first_sub_match_start": 0,
                "first_sub_match_end": len(new_subject),
            }
            pos_trim.append(d)
            # pass

    # Negatives conventionally have full_match=0 & partial_match=0; keep as-is
    # neg_trim = [s for s in neg if s is not None]
    neg_trim = []

    for s in neg:
        if ensure_ascii and not s["subject"].isascii():
            continue

        if len(s["subject"]) >= min_subject_length:
            neg_trim.append(s)

    # Double check the matches are correct
    for s in pos_trim:
        if not rx.match(regex, s["subject"]):
            # Add s to neg_trim
            neg_trim.append(s)
            # Remove s from pos_trim
            pos_trim.remove(s)
    for s in neg_trim:
        if rx.match(regex, s["subject"]):
            # Add s to pos_trim
            pos_trim.append(s)
            # Remove s from neg_trim
            neg_trim.remove(s)

    # Deduplicate by subject within positives and negatives by sampling one per subject
    pos_trim = _sample_unique_by_subject(pos_trim)
    neg_trim = _sample_unique_by_subject(neg_trim)

    pos_trim_double_checked = []
    neg_trim_double_checked = []

    for s in pos_trim:
        try:
            m = rx.search(regex, s["subject"],timeout=3)
            fm = rx.fullmatch(regex, s["subject"],timeout=3)
        except Exception as e:
            continue
        if fm:
            corrected_s = {
                "id": s["id"],
                "subject": fm.group(0),
                "func": s["func"],
                "full_match": 1,
                "partial_match": 1,
                "first_sub_match_start": fm.span()[0],
                "first_sub_match_end": fm.span()[1],
            }

            pos_trim_double_checked.append(corrected_s)
        elif m:
            pass
        else:
            pass

    for s in neg_trim:
        try:
            m = rx.search(regex, s["subject"],timeout=3)
            fm = rx.fullmatch(regex, s["subject"],timeout=3)
        except Exception as e:
            continue
        if fm:
            pass
        elif m:
            pass
        else:
            neg_trim_double_checked.append(s)

    if len(pos_trim_double_checked) < 1 or len(neg_trim_double_checked) < 1:
        return None

    trimmed = dict(row)
    trimmed["positive_strings"] = pos_trim_double_checked
    trimmed["negative_strings"] = neg_trim_double_checked
    return trimmed


def compute_bins(values, n_bins: int):
    """
    Quantile-based bin edges (inclusive on left, exclusive on right except last).
    Ensures strictly increasing edges; if too few unique values, collapse bins.
    Returns list of edges [e0, e1, ..., ek] with k<=n_bins.
    """
    if not values:
        return [0.0, 1.0]
    xs = sorted(values)
    edges = []
    for q in [i / n_bins for i in range(n_bins + 1)]:
        idx = min(len(xs) - 1, max(0, int(round(q * (len(xs) - 1)))))
        edges.append(xs[idx])
    # Ensure strictly increasing
    uniq = [edges[0]]
    for v in edges[1:]:
        if v > uniq[-1]:
            uniq.append(v)
    if len(uniq) == 1:
        # All values equal: make a single-wide bin
        return [uniq[0], uniq[0] + 1]
    return uniq


def assign_bin(value, edges):
    """
    Given edges [e0, e1, ..., ek], return an index b in [0, k-1] s.t. e_b <= v < e_{b+1}
    Last bin is closed on the right.
    """
    k = len(edges) - 1
    if k <= 0:
        return 0
    for i in range(k - 1):
        if edges[i] <= value < edges[i + 1]:
            return i
    return k - 1 if value <= edges[-1] else k - 1


def neyman_allocation(strata_map: dict, target_n: int) -> dict:
    """
    strata_map: key -> list of rows (each row must have '_pos_rate')
    Returns allocation dict key -> n_h with sum == target_n and n_h >= 1 for non-empty strata (if feasible).
    """
    # Compute weights w_h ∝ N_h * S_h, with S_h = std deviation of pos_rate in stratum (population stdev)
    weights = {}
    total_weight = 0.0
    for key, rows in strata_map.items():
        Nh = len(rows)
        if Nh == 0:
            continue
        prates = [r["_pos_rate"] for r in rows]
        if Nh >= 2:
            Sh = pstdev(prates)
        else:
            pbar = prates[0]
            Sh = math.sqrt(pbar * (1 - pbar))
        w = Nh * (Sh if Sh > 0 else 1e-9)
        weights[key] = w
        total_weight += w

    # If all weights are zero (identical pos_rate everywhere), fall back to proportional to Nh
    if total_weight <= 0:
        weights = {k: len(v) for k, v in strata_map.items() if len(v) > 0}
        total_weight = float(sum(weights.values()))

    # Initial fractional allocations
    alloc_frac = {k: (weights[k] / total_weight) * target_n for k in weights.keys()}

    # Floor to ints and track remainders
    alloc_int = {k: int(math.floor(v)) for k, v in alloc_frac.items()}
    remainder = target_n - sum(alloc_int.values())

    # Ensure at least 1 per non-empty stratum if possible
    non_empty = [k for k, rows in strata_map.items() if len(rows) > 0]
    for k in non_empty:
        if alloc_int.get(k, 0) < 1 and remainder > 0:
            alloc_int[k] = 1
            remainder -= 1

    # Distribute remaining samples by largest fractional parts
    if remainder > 0:
        order = sorted(alloc_frac.items(), key=lambda kv: kv[1] - math.floor(kv[1]), reverse=True)
        i = 0
        while remainder > 0 and i < len(order):
            k = order[i][0]
            alloc_int[k] = alloc_int.get(k, 0) + 1
            remainder -= 1
            i = (i + 1) % len(order) if order else 0

    # Clip by stratum size
    for k, rows in strata_map.items():
        if k in alloc_int:
            alloc_int[k] = min(alloc_int[k], len(rows))

    # Final sanity: if sum is low due to clipping, greedily add where possible
    deficit = target_n - sum(alloc_int.values())
    if deficit > 0:
        # Add to strata with most headroom
        headroom = sorted(((k, len(rows) - alloc_int.get(k, 0)) for k, rows in strata_map.items()), key=lambda x: x[1], reverse=True)
        idx = 0
        while deficit > 0 and headroom:
            k, room = headroom[idx % len(headroom)]
            if room > 0:
                alloc_int[k] = alloc_int.get(k, 0) + 1
                deficit -= 1
                headroom[idx % len(headroom)] = (k, room - 1)
            idx += 1

    return alloc_int


# -------------------------- Main pipeline --------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to input NDJSON")
    parser.add_argument("--output", required=True, help="Path to output NDJSON (sample)")
    parser.add_argument("--confidence", type=float, default=0.95, help="Confidence level (default 0.95)")
    parser.add_argument("--min-subject-length", type=int, default=3, help="Minimum subject length to keep in the samples (default 3)")
    parser.add_argument("--ensure-ascii", action="store_true", help="Ensure ASCII-only subjects")
    parser.add_argument("--margin", type=float, default=0.05, help="Margin of error (default 0.05)")
    parser.add_argument("--bins-test", type=int, default=4, help="Quantile bins for test_count (default 4)")
    parser.add_argument("--bins-pos", type=int, default=4, help="Quantile bins for pos_rate (default 4)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--emit-metadata", action="store_true", help="Emit per-row stratification metadata")
    args = parser.parse_args()

    random.seed(args.seed)

    # 1) Read & preprocess
    pre = []
    with open(args.input, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue

            trimmed = trim_row(row, args.min_subject_length, args.ensure_ascii)
            if trimmed is None:
                continue

            # Compute post-trim test_count and pos_rate
            pos = trimmed.get("positive_strings") or []
            neg = trimmed.get("negative_strings") or []
            test_count = len(pos) + len(neg)
            if test_count <= 0:
                continue
            pos_rate = len(pos) / test_count

            trimmed["_project_bucket"] = project_bucket(trimmed)
            trimmed["_test_count"] = test_count
            trimmed["_pos_rate"] = pos_rate
            pre.append(trimmed)

    pre = dedupe_by_strings(pre)

    N = len(pre)
    if N == 0:
        print("No rows left after preprocessing.", file=sys.stderr)
        # Write empty file
        with open(args.output, "w", encoding="utf-8") as out:
            pass
        return

    # 2) Build bins (quantile-based for balance)
    test_edges = compute_bins([r["_test_count"] for r in pre], max(2, args.bins_test))
    pos_edges = compute_bins([r["_pos_rate"] for r in pre], max(2, args.bins_pos))

    # 3) Assign strata
    strata = defaultdict(list)
    for r in pre:
        tb = assign_bin(r["_test_count"], test_edges)
        pb = assign_bin(r["_pos_rate"], pos_edges)
        key = (r["_project_bucket"], tb, pb)
        strata[key].append(r)

    # 4) Determine total sample size
    n_total = cochran_sample_size(N, confidence=args.confidence, margin=args.margin, p=0.5)

    # 5) Neyman allocation across strata
    alloc = neyman_allocation(strata, n_total)

    # 6) Sample within each stratum
    sampled = []
    for key, rows in strata.items():
        n_h = alloc.get(key, 0)
        if n_h <= 0:
            continue
        if n_h >= len(rows):
            chosen = rows[:]  # all
        else:
            chosen = random.sample(rows, n_h)
        sampled.extend(chosen)

    # 7) Emit NDJSON
    with open(args.output, "w", encoding="utf-8") as out:
        for r in sampled:
            # Drop internal fields or emit as metadata
            test_count = r.pop("_test_count")
            pos_rate = r.pop("_pos_rate")
            proj_bucket = r.pop("_project_bucket")
            if args.emit_metadata:
                meta = {
                    "project_bucket": proj_bucket,
                    "test_count": test_count,
                    "pos_rate": pos_rate,
                    "test_count_bin": assign_bin(test_count, test_edges),
                    "pos_rate_bin": assign_bin(pos_rate, pos_edges),
                }
                r = dict(r)
                r["_meta"] = meta
            out.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")

    # 8) Summary to stderr
    # Summaries: population vs sample sizes per bucket
    pop_counts = defaultdict(int)
    samp_counts = defaultdict(int)
    for k, rows in strata.items():
        pop_counts[k] = len(rows)
    for row in sampled:
        pb = project_bucket(row)
        # We need edges again for bins (they were popped only if metadata not emitted)
        tc = len(row["positive_strings"]) + len(row["negative_strings"])
        pr = len(row["positive_strings"]) / max(1, tc)
        k = (pb, assign_bin(tc, test_edges), assign_bin(pr, pos_edges))
        samp_counts[k] += 1

    print(f"Preprocessed population N={N}; target sample n={n_total}; actual sample n={len(sampled)}", file=sys.stderr)
    print("Stratum allocations (project_bucket, test_bin, pos_bin): sampled / population", file=sys.stderr)
    def fmt_bin(edges, i):
        if i >= len(edges)-1: i = len(edges)-2
        return f"[{edges[i]}, {edges[i+1]}{'*' if i==len(edges)-2 else ')'}"
    for k in sorted(pop_counts.keys()):
        proj, tb, pb = k
        sc = samp_counts.get(k, 0)
        pc = pop_counts[k]
        print(f"  {proj:12s}  test:{fmt_bin(test_edges, tb):>15s}  pos:{fmt_bin(pos_edges, pb):>15s}  ->  {sc}/{pc}", file=sys.stderr)


if __name__ == "__main__":
    main()