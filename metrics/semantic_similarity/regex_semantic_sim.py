"""
regex_similarity.py

Compute a symmetric semantic similarity between two regular expressions by:
  1) Generating test strings from BOTH regexes using EGRET (egret_ext).
  2) Evaluating each regex on the UNION of generated strings.
  3) Scoring overlap of their match sets with F1 (default) or Fβ (weighted).
Also returns Jaccard and diagnostic one-way accuracies.

Usage:

    from regex_similarity import symmetrical_semantic_similarity, semantic_similarity

    # Symmetric (F1):
    metrics = symmetrical_semantic_similarity(r"^[a-z]+$", r"[a-z]+")
    print("F1 (match-set): {:.2%}".format(metrics["f1_matchset"]))

    # Weighted (Fβ), e.g. β=2 favors recall of regex1 relative to regex2:
    metrics = symmetrical_semantic_similarity(r"^[a-z]+$", r"[a-z]+", beta=2.0)
    print("Fβ=2 (match-set): {:.2%}".format(metrics["f_beta_matchset"]))

CLI:

    python regex_similarity.py <regex1> <regex2> [--beta 1.0] [--base-substring evil] [--debug]
"""

from __future__ import annotations

import argparse
from typing import Any, Dict, List, Set

import regex as rx
rx.DEFAULT_VERSION = rx.VERSION1

import metrics.semantic_similarity.egret_ext as egret_ext  # type: ignore


# ------------------------------
# EGRET helpers
# ------------------------------

def generate_test_strings(regex: str, base_substring: str = "evil") -> List[str]:
    """
    Uses EGRET via egret_ext.run to generate test strings for the given regex.
    EGRET returns: [alert1, alert2, ..., "BEGIN", test_string1, test_string2, ...]
    We strip everything up to and including the "BEGIN" marker (if present).
    """
    # Signature: run(regex, base_substring, check_mode, web_mode, debug_mode, stat_mode)
    test_list = egret_ext.run(regex, base_substring, False, False, False, False)

    try:
        begin_index = test_list.index("BEGIN")
        return test_list[begin_index + 1:]
    except ValueError:
        # No "BEGIN" marker found; assume entire list are test strings
        return test_list


# ------------------------------
# Internal utilities
# ------------------------------

def _dedupe(seq: List[str]) -> List[str]:
    """Deduplicate while preserving order."""
    return list(dict.fromkeys(seq))

def _compiled(pattern: str) -> rx.Pattern:
    try:
        # Compile without a timeout; timeouts are applied on match operations.
        return rx.compile(pattern)
    except rx.error as e:
        raise ValueError(f"Failed to compile regex '{pattern}': {e}") from e


# ------------------------------
# One-way (diagnostic) accuracy
# ------------------------------

def measure_accuracy(regex_ref: str, regex_other: str, base_substring: str = "evil", debug: bool = False) -> Dict[str, Any]:
    """
    One-way measure: generate test strings from regex_ref, then see how often
    regex_other agrees with regex_ref's accept/reject decisions.

    Returns a dictionary with the confusion counts and accuracy.
    """
    test_strings = generate_test_strings(regex_ref, base_substring=base_substring)
    if debug:
        print(f"[DEBUG] {regex_ref!r} generated {len(test_strings)} strings")

    if not test_strings:
        raise ValueError(f"No test strings generated from reference regex: {regex_ref!r}")

    cref = _compiled(regex_ref)
    cother = _compiled(regex_other)

    accepted_by_ref: List[str] = []
    rejected_by_ref: List[str] = []
    for s in test_strings:
        try:
            if cref.fullmatch(s, timeout=3):
                accepted_by_ref.append(s)
            else:
                rejected_by_ref.append(s)
        except TimeoutError:
            # Skip strings where the reference timed out (no decision)
            continue

    # Evaluate other against reference's decisions
    tp = 0  # accepted by both
    for s in accepted_by_ref:
        try:
            if cother.fullmatch(s, timeout=3):
                tp += 1
        except TimeoutError:
            # Timeout counts as a mismatch (FN) implicitly via subtraction below
            pass

    tn = 0  # rejected by both
    for s in rejected_by_ref:
        try:
            if not cother.fullmatch(s, timeout=3):
                tn += 1
        except TimeoutError:
            # Timeout counts as a mismatch (FP) implicitly via subtraction below
            pass

    fn = len(accepted_by_ref) - tp   # accepted by ref, rejected/timeouts by other
    fp = len(rejected_by_ref) - tn   # rejected by ref, accepted/timeouts by other
    total = len(accepted_by_ref) + len(rejected_by_ref)
    accuracy = (tp + tn) / total if total > 0 else 0.0

    return {
        "regex_ref": regex_ref,
        "regex_other": regex_other,
        "true_positive": tp,
        "false_negative": fn,
        "true_negative": tn,
        "false_positive": fp,
        "total_test_strings": total,
        "accuracy": accuracy,
    }


# ------------------------------
# Symmetric similarity (primary)
# ------------------------------

def symmetrical_semantic_similarity(
    regex1: str,
    regex2: str,
    base_substring: str = "evil",
    beta: float = 1.0,
    debug: bool = False,
) -> Dict[str, Any]:
    """
    Symmetric similarity via overlap of match sets over a SHARED pool S:
      - S = union of EGRET-generated strings from regex1 and regex2
      - A = strings in S matched by regex1
      - B = strings in S matched by regex2

    Returns:
      - f1_matchset: 2|A∩B| / (|A|+|B|)
      - f_beta_matchset: weighted Fβ over (precision, recall) induced by set overlap
      - jaccard_matchset: |A∩B| / |A∪B|
      - coverage_r1_in_r2: |A∩B| / |A|
      - coverage_r2_in_r1: |A∩B| / |B|
      - one_way diagnostics for r1->r2 and r2->r1
      - cardinalities of A, B, A∩B, and |S|
    """
    S1 = generate_test_strings(regex1, base_substring=base_substring)
    S2 = generate_test_strings(regex2, base_substring=base_substring)
    S = _dedupe(S1 + S2)

    if debug:
        print(f"[DEBUG] {regex1!r} produced {len(S1)} strings; {regex2!r} produced {len(S2)} strings; union |S|={len(S)}")

    if not S:
        # If neither side produced strings, define perfect similarity (degenerate)
        return {
            "f1_matchset": 1.0,
            "f_beta_matchset": 1.0,
            "beta": beta,
            "coverage_r1_in_r2": 1.0,
            "coverage_r2_in_r1": 1.0,
            "jaccard_matchset": 1.0,
            "one_way": {
                "r1->r2": {"accuracy": 1.0, "total_test_strings": 0},
                "r2->r1": {"accuracy": 1.0, "total_test_strings": 0},
                "accuracy_mean": 1.0,
            },
            "cardinalities": {"|A|": 0, "|B|": 0, "|A∩B|": 0, "|S|": 0},
        }

    c1 = _compiled(regex1)
    c2 = _compiled(regex2)

    A: Set[str] = set()
    B: Set[str] = set()

    for s in S:
        try:
            if c1.fullmatch(s, timeout=3):
                A.add(s)
        except TimeoutError:
            # Treat timeouts as non-matches for set construction
            pass
        try:
            if c2.fullmatch(s, timeout=3):
                B.add(s)
        except TimeoutError:
            pass

    inter = len(A & B)
    a = len(A)
    b = len(B)

    # Coverages (interpretable as recall vs precision under r1->r2)
    cov_1_in_2 = (inter / a) if a else (1.0 if b == 0 else 0.0)
    cov_2_in_1 = (inter / b) if b else (1.0 if a == 0 else 0.0)

    # Symmetric F1 over match sets
    denom = (a + b)
    f1 = (2 * inter / denom) if denom else 1.0

    # Weighted Fβ (β>1 favors recall of A; β<1 favors precision of B)
    if a == 0 and b == 0:
        f_beta = 1.0
    else:
        P = cov_2_in_1
        R = cov_1_in_2
        if P == 0.0 and R == 0.0:
            f_beta = 0.0
        else:
            beta2 = beta * beta
            f_beta = (1 + beta2) * P * R / (beta2 * P + R)

    # Jaccard over match sets
    union = a + b - inter
    jaccard = (inter / union) if union else 1.0

    # Diagnostic one-way accuracies
    m12 = measure_accuracy(regex1, regex2, base_substring=base_substring, debug=debug)
    m21 = measure_accuracy(regex2, regex1, base_substring=base_substring, debug=debug)
    acc_mean = (m12["accuracy"] + m21["accuracy"]) / 2.0

    return {
        "f1_matchset": f1,
        "f_beta_matchset": f_beta,
        "beta": beta,
        "coverage_r1_in_r2": cov_1_in_2,
        "coverage_r2_in_r1": cov_2_in_1,
        "jaccard_matchset": jaccard,
        "one_way": {"r1->r2": m12, "r2->r1": m21, "accuracy_mean": acc_mean},
        "cardinalities": {"|A|": a, "|B|": b, "|A∩B|": inter, "|S|": len(S)},
    }


# ------------------------------
# One-way wrapper (kept for API)
# ------------------------------

def semantic_similarity(regex_ground: str, regex_test: str, base_substring: str = "evil", debug: bool = False) -> Dict[str, Any]:
    """
    Original one-way measure: generate from regex_ground, see how well regex_test matches.
    """
    return measure_accuracy(regex_ground, regex_test, base_substring=base_substring, debug=debug)


# ------------------------------
# CLI
# ------------------------------

def _format_pct(x: float) -> str:
    return f"{x:.2%}"

def main() -> None:
    parser = argparse.ArgumentParser(description="Symmetric semantic similarity between two regexes using EGRET-generated strings.")
    parser.add_argument("regex1", type=str, help="First regular expression")
    parser.add_argument("regex2", type=str, help="Second regular expression")
    parser.add_argument("--beta", type=float, default=1.0, help="Fβ weighting (β>1 favors recall of regex1; β<1 favors precision of regex2). Default: 1.0 (F1)")
    parser.add_argument("--base-substring", type=str, default="evil", help="EGRET base substring. Default: 'evil'")
    parser.add_argument("--debug", action="store_true", help="Enable debug prints")
    args = parser.parse_args()

    try:
        metrics = symmetrical_semantic_similarity(
            args.regex1, args.regex2,
            base_substring=args.base_substring,
            beta=args.beta,
            debug=args.debug,
        )
    except Exception as e:
        print("Error in symmetric similarity:", e)
        raise SystemExit(2)

    print("=== Symmetric match-set metrics ===")
    print("F1:       ", _format_pct(metrics["f1_matchset"]))
    print(f"Fβ (β={args.beta:g}):", _format_pct(metrics["f_beta_matchset"]))
    print("Jaccard:  ", _format_pct(metrics["jaccard_matchset"]))
    print("Coverage r1 in r2:", _format_pct(metrics["coverage_r1_in_r2"]))
    print("Coverage r2 in r1:", _format_pct(metrics["coverage_r2_in_r1"]))
    print("Cardinalities:", metrics["cardinalities"])

    print("\n=== One-way diagnostic accuracies ===")
    ow = metrics["one_way"]
    print("r1 -> r2 accuracy:", _format_pct(ow["r1->r2"]["accuracy"]), "on", ow["r1->r2"]["total_test_strings"], "strings")
    print("r2 -> r1 accuracy:", _format_pct(ow["r2->r1"]["accuracy"]), "on", ow["r2->r1"]["total_test_strings"], "strings")
    print("Mean accuracy:     ", _format_pct(ow["accuracy_mean"]))


if __name__ == "__main__":
    main()
