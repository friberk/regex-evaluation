# Modules Directory

This directory contains the various code modules that implement the methodology described in this paper. Each subdirectory represents a distinct component of the research pipeline.

## Module Structure

```
modules/
├── evaluator/                # Regex evaluation framework
│   ├── dk.brics.automaton/   # Automata library for regex operations
│   ├── docs/                 # Documentation for the evaluator
│   ├── evaluation/           # Core evaluation logic
│   └── gradle/               # Build system configuration
│
├── extractor/                # Tools for extracting regexes from repositories
│   ├── db/                   # Database operations
│   ├── docs/                 # Documentation for the extractor
│   ├── driver/               # Web driver for scraping
│   ├── dynamic-extraction/   # Runtime extraction of regexes
│   ├── ecosystems-dump/      # Package ecosystem data
│   ├── evaluation/           # Evaluation of extraction process
│   ├── reporting/            # Reporting utilities
│   ├── shared/               # Shared utilities
│   ├── static-extraction/    # Static analysis extraction
│   └── tools/                # Utility tools
│
├── helpfulness_score/        # Implementation of our novel helpfulness metric
│
├── make_plots/               # Scripts for generating paper figures
│
├── regex_semantic_sim/       # Semantic similarity measurement for regexes
│
├── regex_syntactic_sim/      # Syntactic similarity measurement for regexes
│
├── run_analysis/             # Scripts for analyzing experimental results
│   ├── analyze_accuracies.py             # Analyze regex accuracy
│   ├── analyze_helpfulness_score.py      # Analyze helpfulness scores
│   ├── analyze_semantic_similarities.py  # Analyze semantic similarity
│   └── analyze_syntactic_similarities.py # Analyze syntactic similarity
│
└── run_strategies/           # Scripts for running regex composition strategies
    ├── prompts/              # Prompts for LLM-based regex generation
    ├── run_llms.py           # Run LLM-based regex generation
    ├── run_reuse_by_example.md # Documentation for running reuse-by-example
    └── run_synthesizers.py   # Run formal synthesizers
```

## Module Descriptions

### evaluator/

The evaluator module implementing the reuse-by-example approach using a curated database of regexes. The module is built on Java and uses the dk.brics.automaton library for regex operations and automata-based analysis.

### extractor/

The extractor module contains tools for mining regexes from various sources:

1. **Static extraction**: Parse regex patterns from source code
2. **Dynamic extraction**: Capture regex usage at runtime
3. **Web scraping**: Extract regexes from internet sources like RegExLib

This module was used to construct both the RegexCompositionBench dataset and the regex reuse database.

### helpfulness_score/

This module implements our novel "helpfulness" metric, which quantifies how conservative or liberal a regex is compared to the minimum necessary pattern. The score helps evaluate whether regex composition strategies provide solutions that match developer preferences.

### make_plots/

Scripts for generating the visualizations and plots used in the paper, including accuracy comparisons, similarity measurements, and helpfulness score distributions.

### regex_semantic_sim/

Implements methods for measuring the semantic similarity between regular expressions by:
1. Generating test strings for each regex using EGRET
2. Comparing the accept/reject behavior of both regexes on these test strings
3. Computing a symmetrical similarity score

### regex_syntactic_sim/

Calculates the syntactic similarity between regexes using Abstract Syntax Tree (AST) edit distance. It implements the Zhang-Shasha tree edit distance algorithm to measure how structurally similar regex patterns are.

### run_analysis/

Contains scripts for analyzing the performance of different regex composition strategies across multiple dimensions:

1. **Accuracy**: How well regex candidates match the intended patterns
2. **Syntactic Similarity**: How structurally similar regex candidates are to ground truth regexes
3. **Semantic Similarity**: How functionally similar regex candidates are to ground truth regexes
4. **Helpfulness Score**: How conservative or liberal regex candidates are

### run_strategies/

Implements the three main regex composition strategies evaluated in the paper:

1. **Reuse-by-example**: Uses a database of production-ready regexes to find candidates
2. **Formal Synthesizers**: Uses algorithmic approaches like RFixer and FOREST
3. **Large Language Models (LLMs)**: Uses various LLMs to generate regexes from examples

## Pipeline Flow

The modules form a research pipeline that flows through these stages:

1. **Data Collection**: Extract regexes using `extractor` to create datasets and the reuse database
2. **Generation**: Run different composition strategies via `run_strategies` to produce regex candidates
3. **Evaluation**: Assess candidates using `evaluator` and compute similarity metrics via `regex_semantic_sim` and `regex_syntactic_sim`
4. **Analysis**: Process evaluation results using `run_analysis` and generate visualizations with `make_plots`

## Usage

Each module has its own README with specific usage instructions. The general workflow is:

1. Prepare test suites from RegexCompositionBench
2. Run one or more composition strategies to generate regex candidates
3. Evaluate and analyze the generated candidates
4. Compare the results across strategies

## Dependencies

Dependencies vary by module:
- Python 3.9+ (for Python-based modules)
- Java 22 (for Java-based modules)
- Package-specific dependencies are listed in each module's README or requirements.txt
