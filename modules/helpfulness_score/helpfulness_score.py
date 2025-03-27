from pyformlang.finite_automaton.deterministic_finite_automaton import DeterministicFiniteAutomaton
from pyformlang.finite_automaton.state import State
from pyformlang.finite_automaton.symbol import Symbol
from pyformlang.regular_expression import PythonRegex as Regex
import re
import warnings
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
    # print("Regex:", regex_str)
    enfa = Regex(regex_str).to_epsilon_nfa()
    dfa = enfa.to_deterministic()  # no minimization
    if alphabet is not None:
        dfa = complete_dfa_no_min(dfa, alphabet)
    return dfa


def get_automata_transition_count(dfa):
    """Returns the total number of transitions in the DFA."""
    transitions = dfa.get_number_transitions()
    states = len(dfa.states)
    # count = sum(len(trans) for trans in transitions.values())
    return transitions


def calculate_helpfulness_score(candidate_regex, positive_examples, negative_examples):
    """
    Computes a helpfulness score defined as:
        score = 1 - 2 * (|T(candidate)| - |T(candidate ∩ conservative)|) / |T(candidate)|

    In this metric, if the candidate is as liberal as possible (i.e. ".*"),
    then nearly all candidate transitions are outside the conservative part and the ratio is ~1,
    giving a score near -1. A more specific candidate will have a ratio lower than 1 and a higher score.
    """
    alphabet = get_common_alphabet(positive_examples, negative_examples)
    # alphabet = extend_alphabet(positive_examples, negative_examples)

    adapted_candidate_regex = adapt_regex_to_pyformlang(candidate_regex)

    # Build raw (non-minimized) DFA for the candidate.
    candidate_dfa_raw = regex_to_dfa_no_min(adapted_candidate_regex, alphabet)
    candidate_trans = get_automata_transition_count(candidate_dfa_raw)

    consevative_regex = "|".join(positive_examples)
    conservative_regex = "" if consevative_regex == "|" else consevative_regex
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
    # positive_examples = ["a", "b", "c"]
    # print("Positive examples:", positive_examples)
    # negative_examples = ["d"]
    # print("Negative examples:", negative_examples)

    # print()
    # candidate_regex = ".*"  # Most liberal candidate
    # score = calculate_helpfulness_score(candidate_regex, positive_examples, negative_examples)
    # print("Candidate regex:", candidate_regex)
    # print("The helpfulness score of the candidate regex is:", score)

    # candidate_regex = "[a-c]"  # Conservative candidate
    # print("\nCandidate regex:", candidate_regex)
    # print("The helpfulness score of the candidate regex is:", calculate_helpfulness_score(candidate_regex, positive_examples, negative_examples))

    # candidate_regex = "[a-d]"  # Conservative candidate
    # print("\nCandidate regex:", candidate_regex)
    # print("The helpfulness score of the candidate regex is:", calculate_helpfulness_score(candidate_regex, positive_examples, negative_examples))

    # candidate_regex = "[a-e]"  # Conservative candidate
    # print("\nCandidate regex:", candidate_regex)
    # print("The helpfulness score of the candidate regex is:", calculate_helpfulness_score(candidate_regex, positive_examples, negative_examples))

    # candidate_regex = "[a-f]"  # Conservative candidate
    # print("\nCandidate regex:", candidate_regex)
    # print("The helpfulness score of the candidate regex is:", calculate_helpfulness_score(candidate_regex, positive_examples, negative_examples))

    # candidate_regex = "[a-h]"
    # print("\nCandidate regex:", candidate_regex)
    # print("The helpfulness score of the candidate regex is:", calculate_helpfulness_score(candidate_regex, positive_examples, negative_examples))

    # candidate_regex = "[a-z]{99}"
    # print("\nCandidate regex:", candidate_regex)
    # print("The helpfulness score of the candidate regex is:", calculate_helpfulness_score(candidate_regex, positive_examples, negative_examples))

    # positive_examples = ["tekt@hotmail.com", "test@gmail.com"]
    # negative_examples = ["facebook.com", "google.com", "other_stuff"]

    # print()
    # candidate_regex = "^[^\s@]+@([^\s@.,]+\.)+[^\s@.,]{2,}$"
    # print("\nCandidate regex:", candidate_regex)
    # print("The helpfulness score of the candidate regex is:", calculate_helpfulness_score(candidate_regex, positive_examples, negative_examples))

    # candidate_regex = "te.{2}@.com"
    # print("\nCandidate regex:", candidate_regex)
    # print("The helpfulness score of the candidate regex is:", calculate_helpfulness_score(candidate_regex, positive_examples, negative_examples))

    # positive_examples = ["subscribe"]
    # negative_examples = ["threshold", "urlAfterRedirects", "userInfo", "setAttribute", "route", "pppUuuu", "isLoggedIn", "innerHTML", "highlightMenu", "get", "foo", "baz", "bar", "add"]

    # candidate_regex = "\b(rss|feeds?|atom|json|xml|rdf|blogs?|subscribe)\b"
    # print("\nCandidate regex:", candidate_regex)
    # print("The helpfulness score of the candidate regex is:", calculate_helpfulness_score(candidate_regex, positive_examples, negative_examples))

    # positive_examples = ["790d2cf6ada1937726c17f1ef41ab125"]
    # negative_examples = ["790D2CF6ADA1937726C17F1EF41AB125","790d2cf6ada1937726c17f1ef41ab125f6k"]
    # candidate_regex = "^(0x)?[0-9a-f]*$"

    # print("\nCandidate regex:", candidate_regex)
    # print("The helpfulness score of the candidate regex is:", calculate_helpfulness_score(candidate_regex, positive_examples, negative_examples))

    # positive_examples = ["790d2cf6ada1937726c17f1ef41ab125"]
    # negative_examples = ["790D2CF6ADA1937726C17F1EF41AB125","790d2cf6ada1937726c17f1ef41ab125f6k"]
    # candidate_regex = "^([a-z0-9]{32})$"

    # print("\nCandidate regex:", candidate_regex)
    # print("The helpfulness score of the candidate regex is:", calculate_helpfulness_score(candidate_regex, positive_examples, negative_examples))

    # positive_examples = ["23.30", "23:30"]
    # negative_examples = ["23-30"]

    # candidate_regex = "([\d.]+)(?:~)?([\d.]+)?(?::)?([\d.]+)?"

    # print("\nCandidate regex:", candidate_regex)
    # print("The helpfulness score of the candidate regex is:", calculate_helpfulness_score(candidate_regex, positive_examples, negative_examples))

    #     Pos Str=
    # 123-456-7890
    # (123) 456-7890
    # 123 456 7890
    # 123.456.7890
    # +91 (123) 456-7890
    positive_examples = [r"123-456-7890", r"(123) 456-7890", r"123 456 7890", r"123.456.7890", r"\+91 (123) 456-7890"]
    # Neg
    # Neg Str=
    # 555-555-555554 -> Fail
    # 123-4567 -> Fail
    negative_examples = [r"555 555 555554", r"123 4567"]

    candidate_regex = r"^\(?\d+\)?[-.\s]?\d+[-.\s]?\d+$"

    print("\nCandidate regex:", candidate_regex)
    print("The helpfulness score of the candidate regex is:", calculate_helpfulness_score(candidate_regex, positive_examples, negative_examples))


if __name__ == "__main__":
    main()
