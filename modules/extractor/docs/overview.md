
# Regex Extraction Overview

This documentation gives an overview of the regex extractor. It outlines why it was conceived, what information we are
trying to extract, and how the system works.

## Reuse Background
In our research project, we are trying to determine if regexes written in production environments can be reused across
different projects. We say regex *A* can be reused in regex *B*'s place if regex *A* satisfies the same requirements as
*B*. It is worth noting that we are not trying to find *semantically identical* regexes. Rather, we want regexes that can
be dropped in and keep the program operating correctly. For example, consider the following regexes:
```regexp
A: \w+
B: [A-Za-z0-9_]+
C: [A-Za-z]+
```

In this example, regexes A and B are syntactically different yet semantically identical. They will behave in the exact
same way. However, regexes B and C are similar yet not semantically identical - B matches numbers and underscores. That
being said, let's say that C's purpose is to accept letters and reject special characters. It might be used like this:
```typescript
const acceptCharacters = (input: string) => /[A-Za-z]+/.test(input) // regex C in action

acceptCharacters('abcdeADEF') // true
acceptCharacters('ASDF') // true
acceptCharacters('*&^%') // false - contains special characters
acceptCharacters('defkjso*&^%ASDJKFLE') // false - contains special characters
acceptCharacters('') // false - must not be empty
```
If these example strings are all we know about `acceptCharacters`'s behavior, then regex B is a perfect drop in
replacement for C because B will correctly accept and reject the same strings as C. So, the original authors of the
above code block could have reused B from some other source instead of writing their own regex C.

Reuse gets slightly more complicated though, because not all regexes behave in the same way. Within our above example,
consider the input string `'hello_world'`. Would the authors have wanted to accept or reject this string? If it
supposed to be rejected, then reusing B would break the program semantics. If it should be accepted, the reusing B
caught an edge case that the programmer missed.

## Evaluation Design
To determine if regexes can be reused, we want to find out if there are two production regexes from separate projects
that behave similarly. We also want to compare reuse performance against regex synthesis via classical approaches and
LLMs.

Our evaluation will involve the following steps:
1. Collect production regexes from open source projects written in popular languages.
2. Determine the semantics/behavior of each regex in our corpus.
3. For any regex in an open source project, measure how many other regexes there are from other projects that behave
similarly to the original regex. Likewise, determine if a regex can be synthesized to satisfy the same requirements as
the original regex.
4. If a high proportion of regexes can be replaced by a synthesized regex, then we can argue that synthesis is a viable
reuse approach. If a high proportion of regexes can be replaced by a regex from our corpus, then we can argue that reuse
is an effective approach. We can also compare the effectiveness of synthesis vs. reuse.

## Evaluation Method
To perform our evaluation, we use the following method:

1. To collect production regexes, we statically extract regexes from production source artifacts. We use ecosystems to
get a set of source packages to investigate. We specifically look at JavaScript, Java, and Python packages as these
languages are the most popular. For each project in the dump, we download the source and use language-specific parsers
to extract all statically-written regexes from that source project. We store these regexes in a database along with
metadata about where the regex came from and what source language originated it.
2. We approximate the semantics of a regex by determining which strings are evaluated on a regex in the project's test
suite. Essentially, we orchestrate the runtime environment so that the regex's inputs are logged while we run the test
suite of that project. Running the test suite produces a set of positive (matching) and negative (not matching) strings
for each regex.
3. To actually evaluate the performance of our reuse paradigms, we do the following:
   * Reuse: for each regex in each project, find all regexes from other projects that match this regex's test suite.
   That is, find all other regexes that match all positive strings and reject all negative strings.
   * Synthesis: given each regex's test suite, synthesize a regex for that test suite and determine if it behaves the
   same.

