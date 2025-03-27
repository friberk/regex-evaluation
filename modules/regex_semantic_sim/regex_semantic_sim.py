
"""
regex_similarity.py

A Python library to compute the semantic similarity between two regular expressions.
It uses EGRET (via its Python extension module, egret_ext) as a dependency to generate
test strings from each regex. Then it computes:

1. A symmetric similarity measure for the overall accept/reject behavior.
2. A capture group similarity measure - the average overlap between the captured
   content of the regexes over test strings.

Usage:

    from regex_similarity import (
        symmetrical_semantic_similarity,
        capture_group_similarity
    )

    metrics = symmetrical_semantic_similarity(r"^[a-z]+$", r"[a-z]+")
    group_metrics = capture_group_similarity(r"^(?P<word>[a-z]+)$", r"^(?P<word>[a-z]+)$")

    print("Symmetric similarity: {:.2%}".format(metrics["symmetric_accuracy"]))
    print("Capture group similarity:", group_metrics)
"""

import re
import egret_ext  # type: ignore
from collections import namedtuple
from contextlib import contextmanager
from signal import alarm, signal, SIGALRM

CG = namedtuple("CG", ["start_idx", "end_idx", "content"])

# Regex with timeouts
@contextmanager
def timeout(seconds):
    def handler(signum, frame):
        raise TimeoutError('Regex operation timed out.')

    signal(SIGALRM, handler)
    alarm(seconds)
    try:
        yield
    finally:
        alarm(0)

def exec_regex_with_timeout(regex, string, mode, timeout_seconds=10):
    """Execute a regex with a timeout."""
    try:
        with timeout(timeout_seconds):
            if mode == "full_match":
                match = re.fullmatch(regex, string)
            else:
                match = re.search(regex, string)
            return match
    except TimeoutError:
        raise TimeoutError('Regex operation timed out.')

def generate_test_strings(regex, base_substring="evil"):
    """
    Uses EGRET (via egret_ext.run) to generate test strings for the given regex.
    EGRET returns a list of strings that include any alerts followed by a marker "BEGIN"
    and then the generated strings.

    This function removes the alerts and marker and returns only the test strings.
    """
    # The signature of egret_ext.run is: run(regex, base_substring, check_mode, web_mode, debug_mode, stat_mode)
    test_list = egret_ext.run(regex, base_substring, False, False, False, False)

    # EGRET's output format: [alert1, alert2, ..., "BEGIN", test_string1, test_string2, ...]
    try:
        begin_index = test_list.index("BEGIN")
        return test_list[begin_index + 1:]
    except ValueError:
        # If no "BEGIN" marker is found, assume the entire list are test strings
        return test_list


def measure_accuracy(regex_ref, regex_other, base_substring="evil"):
    """
    One-way measure: generate test strings from regex_ref, then see how often
    regex_other agrees with regex_ref's accept/reject decisions.

    Returns a dictionary with the confusion matrix and accuracy.
    """
    # Generate test strings from the "reference" regex
    test_strings = generate_test_strings(regex_ref, base_substring=base_substring)
    print("Test strings:", test_strings)
    if not test_strings:
        raise ValueError("No test strings generated from reference regex: {}".format(regex_ref))

    # Compile both regexes
    try:
        compiled_ref = re.compile(regex_ref)
    except re.error as e:
        raise ValueError("regex_ref did not compile: {}".format(e))

    try:
        compiled_other = re.compile(regex_other)
    except re.error as e:
        raise ValueError("regex_other did not compile: {}".format(e))

    # Split test strings into accepted vs. rejected by regex_ref
    accepted_by_ref = []
    rejected_by_ref = []
    for s in test_strings:
        try:
            if exec_regex_with_timeout(compiled_ref, s, "full_match"):
                accepted_by_ref.append(s)
            else:
                rejected_by_ref.append(s)
        except TimeoutError:
            continue

    tp = 0  # accepted by both
    for s in accepted_by_ref:
        try:
            if exec_regex_with_timeout(compiled_other, s, "full_match"):
                tp += 1
        except TimeoutError:
            continue

    tn = 0  # rejected by both
    for s in rejected_by_ref:
        try:
            if not exec_regex_with_timeout(compiled_other, s, "full_match"):
                tn += 1
        except TimeoutError:
            continue

    # Now see if regex_other agrees
    fn = len(accepted_by_ref) - tp   # accepted by ref, rejected by other
    fp = len(rejected_by_ref) - tn   # rejected by ref, accepted by other

    total = len(test_strings)
    accuracy = (tp + tn) / total if total > 0 else 0.0

    return {
        "regex_ref": regex_ref,
        "regex_other": regex_other,
        "true_positive": tp,
        "false_negative": fn,
        "true_negative": tn,
        "false_positive": fp,
        "total_test_strings": total,
        "accuracy": accuracy
    }


def symmetrical_semantic_similarity(regex1, regex2, base_substring="evil"):
    """
    Two-way (symmetric) similarity measure.

    1. Generate test strings from regex1, measure accuracy of regex2 vs. regex1 -> measure1
    2. Generate test strings from regex2, measure accuracy of regex1 vs. regex2 -> measure2
    3. Compute an average or other combination of these two accuracies as 'symmetric_accuracy'.

    Returns a dictionary with measure1, measure2, and symmetric_accuracy.
    """
    # Pass 1: from regex1 -> measure how well regex2 replicates regex1
    measure1 = measure_accuracy(regex1, regex2, base_substring=base_substring)

    # Pass 2: from regex2 -> measure how well regex1 replicates regex2
    measure2 = measure_accuracy(regex2, regex1, base_substring=base_substring)

    # Combine the two one-way accuracies
    symmetric_accuracy = (measure1["accuracy"] + measure2["accuracy"]) / 2.0

    return {
        "measure_ground->test": measure1,
        "measure_test->ground": measure2,
        "symmetric_accuracy": symmetric_accuracy
    }


def semantic_similarity(regex_ground, regex_test, base_substring="evil"):
    """
    Original one-way measure: generate from regex_ground, see how well regex_test matches.
    """
    return measure_accuracy(regex_ground, regex_test, base_substring)

def capture_group_similarity(regex1, regex2, base_substring="evil"):
    """
    Computes a similarity score for the capture groups between two regexes,
    treating regex1 as the ground truth and regex2 as the candidate.

    For each test string in the union of test strings generated from both regexes:
      - If regex1 matches and produces capturing groups, then:
         * If regex2 fails to match, score = 0.
         * Otherwise, extract the captured groups from both.
           Let G_ground be the set of captured groups from regex1,
           and let G_candidate be the set of captured groups from regex2.
           The score for that instance is (|G_ground ∩ G_candidate| / |G_ground|).
      - If regex1 does NOT match:
          * If regex2 matches (i.e. candidate erroneously captures on a string
            that ground truth rejects), then score = 0.
          * If neither matches, skip the instance.

    The overall capture group similarity is the average score across all
    "comparable" instances.

    Returns a dictionary with:
      - "capture_group_similarity": the average similarity over all comparable instances,
      - "num_test_strings": total unique test strings,
      - "num_comparable": number of comparable instances.

    Examples (python3 regex_semantic_sim.py <ground_truth> <candidate>):
    python3 regex_semantic_sim.py "(a|b)" "(a)|b" # Capture group similarity: 50.00%
    python3 regex_semantic_sim.py "(a|b)" "a|b" # Capture group similarity: 0.00%
    """

    # Generate test strings from both regexes
    test_strings1 = generate_test_strings(regex1, base_substring=base_substring)
    test_strings2 = generate_test_strings(regex2, base_substring=base_substring)
    test_strings = list(set(test_strings1).union(set(test_strings2)))

    try:
        compiled1 = re.compile(regex1)
        compiled2 = re.compile(regex2)
    except re.error as e:
        raise ValueError("Regex compilation error: {}".format(e))

    instance_scores = []
    num_comparable = 0

    for s in test_strings:
        m1 = compiled1.fullmatch(s)
        m2 = compiled2.fullmatch(s)

        # Only do the evaluation if both regexes are comparable on this test string.
        if not m1:
            continue

        if not m2:
            continue

        # Extract ground truth capture groups.
        # Prefer named groups if available; otherwise use all groups.
        if m1.groupdict():
            groups_m1 = {k: k for k in m1.groupdict().keys()}
        elif m1.groups():
            # Group numbers start at 1
            groups_m1 = {str(i): i for i in range(1, len(m1.groups()) + 1)}
        else:
            groups_m1 = {}

        if m2.groupdict():
            groups_m2 = {k: k for k in m2.groupdict().keys()}
        elif m2.groups():
            groups_m2 = {str(i): i for i in range(1, len(m2.groups()) + 1)}
        else:
            groups_m2 = {}

        if groups_m1 and not groups_m2:
            num_comparable += 1
            instance_scores.append(0.0)
        elif not groups_m1 and groups_m2:
            continue
        elif not groups_m1 and not groups_m2:
            continue
        else: # groups_m1 and groups_m2
            named_tuple_groups_m1 = set(
                CG(
                    start_idx=m1.start(key),
                    end_idx=m1.end(key),
                    content=m1.group(key)
                )
                for key in groups_m1.values()
            )
            named_tuple_groups_m2 = set(
                CG(
                    start_idx=m2.start(key),
                    end_idx=m2.end(key),
                    content=m2.group(key)
                )
                for key in groups_m2.values()
            )

            match_count = sum(1 for g1 in named_tuple_groups_m1 if g1 in named_tuple_groups_m2)
            instance_score = match_count / len(named_tuple_groups_m1)
            num_comparable += 1
            instance_scores.append(instance_score)

    if num_comparable == 0:
        return {
            "capture_group_similarity": None,
            "num_test_strings": len(test_strings),
            "num_comparable": 0,
        }

    capture_group_similarity = sum(instance_scores) / num_comparable
    return {
        "capture_group_similarity": capture_group_similarity,
        "num_test_strings": len(test_strings),
        "num_comparable": num_comparable
    }

# Example usage when run as a script:
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python regex_similarity.py <regex1> <regex2>")
        print("This will compute the symmetric similarity between the two.")
        sys.exit(1)

    r1 = sys.argv[1]
    r2 = sys.argv[2]

    try:
        metrics = symmetrical_semantic_similarity(r1, r2)
        print("Symmetric similarity: {:.2%}".format(metrics['symmetric_accuracy']))
        print("Detailed results for each direction:")
        print("  1) Regex1 -> Regex2:", metrics["measure_ground->test"])
        print("  2) Regex2 -> Regex1:", metrics["measure_test->ground"])
    except Exception as e:
        print("Error in symmetric similarity:", e)

    try:
        group_metrics = capture_group_similarity(r1, r2)
        if group_metrics["capture_group_similarity"] is not None:
            print("Capture group similarity: {:.2%}".format(group_metrics['capture_group_similarity']))
        else:
            print("Capture group similarity: Not available (no comparable capture groups).")
        print("Detailed group metrics:", group_metrics)
    except Exception as e:
        print("Error in capture group similarity:", e)

    print("=========================================================")

    print("All results combined:")
    metrics.update(group_metrics)
    for k, v in metrics.items():
        print(k, ":", v)
