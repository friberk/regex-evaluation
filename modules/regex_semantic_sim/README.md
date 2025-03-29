# Regex Semantic Similarity

This module provides methods for measuring the semantic similarity between regular expressions.

## Overview

When comparing different regex composition strategies, it's important to evaluate not just whether regexes match the same test cases, but how semantically similar they are to the ground truth or developer intent. This module implements metrics to quantify this similarity.

The semantic similarity is measured by:

1. Generating test strings for each regex using EGRET
2. Comparing the accept/reject behavior of both regexes on these test strings

## Symmetrical Semantic Similarity

This is a bidirectional measure that evaluates how well two regexes match the same strings:

- Generate test strings from regex1, measure how well regex2 replicates regex1's behavior
- Generate test strings from regex2, measure how well regex1 replicates regex2's behavior
- Compute the average of these two measurements

This approach prevents false assessments of similarity that might occur with a unidirectional approach. For example, if regex1 = `/a*/` and regex2 = `/a* | b*/`, a one-way evaluation from regex1 to regex2 would show perfect similarity since regex2 matches all strings that regex1 does. However, regex2 also accepts additional strings that regex1 does not, making them semantically different.

## Technical Implementation

The module relies on:
- EGRET (Evil Generation of Regular Expression Test cases) for generating test strings
- Python's re module for regex matching and analysis
- Custom timeout handling to prevent regex catastrophic backtracking

## Usage

### Requirements

- Python 3.9 or higher
- In order to run this script you need to obtain the shared library produced by compiling EGRET. We included two precompiled ones (i.e., egret_ext.cpython-310-x86_64-linux-gnu.so and egret_ext.cpython-311-x86_64-linux-gnu.so) for Python 3.10 and 3.11. However, we cannot guarantee that these will work on all systems. If the provided precompiled libraries don't work for your system, you will need to compile EGRET yourself. Please see the details in the [EGRET repository](https://github.com/elarsonSU/egret)

### API

```python
from regex_semantic_sim import symmetrical_semantic_similarity, capture_group_similarity

# Compute symmetric similarity between two regexes
metrics = symmetrical_semantic_similarity(r"^[a-z]+$", r"[a-z]+")
print(f"Symmetric similarity: {metrics['symmetric_accuracy']:.2%}")

# Compute capture group similarity (if regexes use capture groups)
group_metrics = capture_group_similarity(r"^(?P<word>[a-z]+)$", r"^(?P<word>[a-z]+)$")
print(f"Capture group similarity: {group_metrics['capture_group_similarity']:.2%}")
```

### Command Line Interface

The module can also be used directly from the command line:

```bash
python regex_semantic_sim.py "^[a-z]+$" "[a-z]+"
```
