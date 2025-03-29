from pyformlang.finite_automaton.deterministic_finite_automaton import DeterministicFiniteAutomaton
from pyformlang.finite_automaton.state import State
from pyformlang.finite_automaton.symbol import Symbol
from pyformlang.regular_expression import PythonRegex as Regex
import re
import warnings
import argparse
import sys

warnings.filterwarnings("ignore")

ALPHABET = [chr(i) for i in range(32, 127)]

def adapt_regex_to_pyformlang(regex: str) -> str:
    """
    Adapts a Python regex into a form that is compatible with pyformlang.

    This function handles several common incompatibilities:
      - Converts shorthand character classes:
          \d  -> [0-9]
          \D  -> [^0-9]
          \s  -> [ \t\r\n\f\v]
          \S  -> [^ \t\r\n\f\v]
          \w  -> [a-zA-Z0-9_]
          \W  -> [^a-zA-Z0-9_]
      - Replaces non-capturing groups (?:...) with capturing groups (...).
      - Removes inline flags (like (?i:...) or standalone (?i)).

    Unsupported constructs that are not regular (and thus not convertible) trigger an error:
      - Lookaheads (?=...) and (?!...)
      - Lookbehinds (?<=...) and (?<!...)
      - Backreferences (e.g., \1, \2, etc.)

    Args:
        regex: The original Python regex string.

    Returns:
        A modified regex string that is more likely to be compatible with pyformlang.

    Raises:
        ValueError: If the regex contains unsupported non-regular constructs.
    """
    # Check for unsupported constructs.
    unsupported_patterns = [
         r"\(\?=",   # positive lookahead
         r"\(\?!",   # negative lookahead
         r"\(\?<=",  # positive lookbehind
         r"\(\?<!",  # negative lookbehind
         r"\\[1-9]"  # backreferences (e.g., \1, \2, ...)
    ]
    for pat in unsupported_patterns:
         if re.search(pat, regex):
             raise ValueError(f"Regex contains unsupported construct: {pat}")

    adapted = regex

    # Convert digit shorthand
    adapted = adapted.replace(r"\d", "[0-9]")
    adapted = adapted.replace(r"\D", "[^0-9]")

    # Convert whitespace shorthand
    adapted = adapted.replace(r"\s", "[ \t\r\n\f\v]")
    adapted = adapted.replace(r"\S", "[^ \t\r\n\f\v]")

    # Convert word character shorthand
    adapted = adapted.replace(r"\w", "[a-zA-Z0-9_]")
    adapted = adapted.replace(r"\W", "[^a-zA-Z0-9_]")

    # Replace non-capturing groups (?:...) with capturing groups (...)
    adapted = re.sub(r"\(\?:", "(", adapted)

    # Remove inline flags for groups, e.g. (?i:...) becomes (
    adapted = re.sub(r"\(\?[imxs]+:", "(", adapted)

    # Remove standalone inline flag groups like (?i) or (?m)
    adapted = re.sub(r"\(\?[imxs]+\)", "", adapted)

    return adapted

def get_common_alphabet(positive_examples, negative_examples):
    """Returns the set of symbols (characters) from the examples."""
    alphabet = set()
    for example in positive_examples + negative_examples:
        for char in example:
            if char == '-':
                alphabet.add(r"\-")
            alphabet.add(char)
    return alphabet

def extend_alphabet(positive_examples, negative_examples):
    """Extends the alphabet with symbols from the examples."""
    alp = ALPHABET.copy()
    for example in positive_examples + negative_examples:
        for char in example:
            if char not in alp:
                alp.append(char)
    return alp

def complete_dfa(dfa, alphabet):
    """
    Returns a complete DFA (with all transitions, using a dead state) and minimizes it.
    """
    complete = DeterministicFiniteAutomaton()
    complete.add_start_state(dfa.start_state)
    for final_state in dfa.final_states:
        complete.add_final_state(final_state)

    transitions = dfa.to_dict()  # state -> {Symbol: state}
    for state, trans in transitions.items():
        for sym, next_state in trans.items():
            if not isinstance(sym, Symbol):
                sym = Symbol(sym)
            complete.add_transition(state, sym, next_state)

    dead_state = State("dead")
    complete_dict = complete.to_dict()
    for state in list(dfa.states):
        for a in alphabet:
            symbol_obj = Symbol(a)
            state_trans = complete_dict.get(state, {})
            if symbol_obj not in state_trans:
                complete.add_transition(state, symbol_obj, dead_state)

    for a in alphabet:
        symbol_obj = Symbol(a)
        complete.add_transition(dead_state, symbol_obj, dead_state)

    return complete.minimize()


def complete_dfa_no_min(dfa, alphabet):
    """Same as complete_dfa but without final minimization (for raw size measurements)."""
    complete = DeterministicFiniteAutomaton()
    complete.add_start_state(dfa.start_state)
    for final_state in dfa.final_states:
        complete.add_final_state(final_state)

    transitions = dfa.to_dict()
    for state, trans in transitions.items():
        for sym, next_state in trans.items():
            if not isinstance(sym, Symbol):
                sym = Symbol(sym)
            complete.add_transition(state, sym, next_state)

    dead_state = State("dead")
    complete_dict = complete.to_dict()
    for state in list(dfa.states):
        for a in alphabet:
            symbol_obj = Symbol(a)
            state_trans = complete_dict.get(state, {})
            if symbol_obj not in state_trans:
                complete.add_transition(state, symbol_obj, dead_state)

    for a in alphabet:
        symbol_obj = Symbol(a)
        complete.add_transition(dead_state, symbol_obj, dead_state)

    return complete  # no minimization


def regex_to_min_dfa(regex_str, alphabet=None):
    """Converts a regex string into a minimized DFA, completed over alphabet if provided."""
    enfa = Regex(regex_str).to_epsilon_nfa()
    dfa = enfa.to_deterministic().minimize()
    if alphabet is not None:
        dfa = complete_dfa(dfa, alphabet)
    return dfa


def regex_to_dfa_no_min(regex_str, alphabet=None):
    """Converts a regex string into a raw (non-minimized) DFA, completed over alphabet if provided."""
    enfa = Regex(regex_str).to_epsilon_nfa()
    dfa = enfa.to_deterministic()  # no minimization
    if alphabet is not None:
        dfa = complete_dfa_no_min(dfa, alphabet)
    return dfa


def get_automata_transition_count(dfa):
    """Returns the total number of transitions in the DFA."""
    transitions = dfa.get_number_transitions()
    return transitions


def calculate_helpfulness_score(candidate_regex, positive_examples, negative_examples, verbose=False):
    """
    Computes a helpfulness score defined as:
        score = 1 - 2 * (|T(candidate)| - |T(candidate ∩ conservative)|) / |T(candidate)|

    In this metric, if the candidate is as liberal as possible (i.e. ".*"),
    then nearly all candidate transitions are outside the conservative part and the ratio is ~1,
    giving a score near -1. A more specific candidate will have a ratio lower than 1 and a higher score.

    Args:
        candidate_regex: The regex pattern to evaluate
        positive_examples: List of strings that should match the regex
        negative_examples: List of strings that should not match the regex
        verbose: Whether to print detailed information during calculation

    Returns:
        A score between -1 (most liberal) and 1 (most conservative)
    """
    alphabet = get_common_alphabet(positive_examples, negative_examples)

    adapted_candidate_regex = adapt_regex_to_pyformlang(candidate_regex)

    # Build raw (non-minimized) DFA for the candidate.
    candidate_dfa_raw = regex_to_dfa_no_min(adapted_candidate_regex, alphabet)
    candidate_trans = get_automata_transition_count(candidate_dfa_raw)

    conservative_regex = "|".join(positive_examples)
    conservative_regex = "" if conservative_regex == "|" else conservative_regex
    # Build minimized conservative DFA from the positive examples.
    conservative_dfa = regex_to_min_dfa(conservative_regex, alphabet)
    candidate_conservative_intersect = candidate_dfa_raw.get_intersection(conservative_dfa)
    candidate_conservative_trans = get_automata_transition_count(candidate_conservative_intersect)

    # print("Candidate transitions:", candidate_trans)
    # print("Candidate ∩ Conservative transitions:", candidate_conservative_trans)

    # Define R as the fraction of candidate transitions that lie outside the conservative part.
    R = min(candidate_trans, candidate_conservative_trans) / candidate_trans if candidate_trans > 0 else 0
    # Map R in [0, 1] to a score in [-1, 1] with a more liberal candidate (R ~ 1) giving -1.
    score = 1 - 2 * R
    return score

def main():
    parser = argparse.ArgumentParser(
        description='Calculate the helpfulness score for a regex pattern based on positive and negative examples. '
                    'This score measures how conservative or liberal a regex pattern is relative to the minimum necessary pattern.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('regex', help='The regex pattern to evaluate')
    parser.add_argument('--positive', '-p', nargs='+', required=True,
                        help='List of positive example strings that should match the regex')
    parser.add_argument('--negative', '-n', nargs='+', default=[],
                        help='List of negative example strings that should not match the regex')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Print detailed information during calculation')

    # Add examples to help text
    parser.epilog = '''
Examples:
  # Calculate score for email regex
  python helpfulness_score.py "^[^\\s@]+@([^\\s@.,]+\\.)+[^\\s@.,]{2,}$" -p "test@example.com" "user@domain.org" -n "invalid" "no-at-sign.com"

  # Calculate score for phone number regex
  python helpfulness_score.py "^\\(?\d+\\)?[-.\s]?\\d+[-.\s]?\\d+$" -p "123-456-7890" "(123) 456-7890" "123.456.7890" -n "555 555 555554" "123 4567"
'''

    args = parser.parse_args()

    if args.verbose:
        print("Positive examples:", args.positive)
        print("Negative examples:", args.negative)
        print("Candidate regex:", args.regex)

    try:
        score = calculate_helpfulness_score(args.regex, args.positive, args.negative, args.verbose)
        print(f"Helpfulness score: {score:.4f}")
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())