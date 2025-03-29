# Regex Syntactic Similarity

This module calculates the syntactic similarity between regexes by computing the tree edit distance between their Abstract Syntax Trees (ASTs).

## Overview

While semantic similarity (implemented in the `regex_semantic_sim` module) measures how similar regexes are in terms of the strings they match, syntactic similarity measures how structurally similar their implementations are. This is important for understanding whether different regex composition strategies produce solutions that resemble those written by developers.

The module implements the Zhang-Shasha tree edit distance algorithm to calculate the minimum number of operations (insertions, deletions, and substitutions) required to transform one regex's AST into another's. The distance is then normalized by the size of the larger tree to produce a value between 0 and 1, where lower values indicate greater similarity.

## Technical Implementation

The module works in several steps:

1. Parse each regex into an AST using a PCRE grammar parser
2. Convert the AST nodes into a format compatible with the Zhang-Shasha algorithm
3. Calculate the tree edit distance between the two ASTs
4. Normalize the distance by the size of the larger tree

This approach allows us to quantify the structural similarity between regexes, even when they are semantically equivalent but expressed differently.

## Requirements

- Python 3.9 or higher
- antlr4-python3-runtime: For parsing regexes into ASTs
- zss: Implementation of the Zhang-Shasha tree edit distance algorithm

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```python
from regex_syntactic_sim.distance import edit_distance

# Calculate edit distance between two regexes
result = edit_distance(r"^[a-z]+$", r"[a-z]+")

# Access the results
print(f"Raw edit distance: {result['ast_edit_distance']}")
print(f"Normalized edit distance: {result['normalized_ast_edit_distance']}")
```
