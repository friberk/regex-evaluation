
# Evaluation

This package holds code related to actually conducting our evaluation.

## The Big Picture

* We have the universe U of all packages we mined
* Package Sample: Sample packages we want to evaluate. In each package P of this sample:
  * P has N regexes. For each regex R, we have:
    * Test Suite: All string examples used w/ R
    * Ground truth: R itself
  * Evaluation context: All regexes S that:
    * Come from all projects in the set U \ P

Output
Test Case: { Examples[ ] (+/-), ground truth regex, package We need this for U\P }
