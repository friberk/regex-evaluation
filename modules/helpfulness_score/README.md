# Helpfulness Score

This module implements the novel "helpfulness" metric introduced in the paper. The helpfulness score quantifies how conservative or liberal a regex pattern is relative to the minimum pattern necessary to match positive examples.

## Overview

When developing regexes, engineers struggle with finding the right balance between patterns that are too conservative (rejecting valid inputs) or too liberal (accepting malformed data). The helpfulness score provides a numerical measure of this balance:

- **Score range**: -1 to 1
- **-1**: Highly liberal regex (matches many strings beyond the positive examples)
- **0**: Balanced regex
- **1**: Highly conservative regex (matches mostly just the positive examples)

## Technical Implementation

The score is computed by comparing the candidate regex with a "conservative" regex built from the positive examples:

1. Convert both regexes to deterministic finite automata (DFAs)
2. Find the intersection of the candidate DFA and the conservative DFA
3. Calculate the ratio of transitions in the intersection to the total transitions in the candidate DFA
4. Map this ratio to a score in the range [-1, 1]

Mathematically, the score is defined as:

```
score = 1 - 2 * min(|T(R)|, |T(R ∩ R')|) / |T(R)|
```

where:
- R is the candidate regex
- R' is the conservative regex (essentially a union of all positive examples)
- T(R) represents the number of transitions in the DFA for regex R

## Usage

### Requirements

- Python 3.9 or higher
- PyFormLang library (install via `pip install pyformlang`)

### Command Line Interface

```bash
python helpfulness_score.py REGEX --positive STR [STR ...] [--negative STR [STR ...]] [--verbose]
```

Arguments:
- `REGEX`: The regex pattern to evaluate
- `--positive`, `-p`: List of positive example strings that should match the regex
- `--negative`, `-n`: List of negative example strings that should not match the regex (optional)
- `--verbose`, `-v`: Print detailed information during calculation

### Examples

Calculate the helpfulness score for an email regex:

```bash
python helpfulness_score.py "^[^\s@]+@([^\s@.,]+\.)+[^\s@.,]{2,}$" \
  --positive "test@example.com" "user@domain.org" \
  --negative "invalid" "no-at-sign.com"
```

Calculate the helpfulness score for a phone number regex:

```bash
python helpfulness_score.py "^\(?\d+\)?[-.\s]?\d+[-.\s]?\d+$" \
  --positive "123-456-7890" "(123) 456-7890" "123.456.7890" \
  --negative "555 555 555554" "123 4567"
```
