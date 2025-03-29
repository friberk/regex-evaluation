# Run Strategies

This directory contains the implementation of the three regex composition strategies evaluated in the paper. The scripts allow you to run the different strategies on regex composition tasks from RegexCompositionBench.

## Overview

The three main regex composition strategies implemented here are:

1. **Reuse-by-example**: Uses a database of production-ready regexes to find candidates that match the given examples
2. **Formal Synthesizers**: Uses algorithmic approaches to generate regexes from examples
3. **Large Language Models (LLMs)**: Uses state-of-the-art language models to generate regexes from examples

Each approach takes the same input format (test suites with positive and negative examples) and produces regex candidates that aim to satisfy these examples.

## Directory Contents

- `prompts/`: Contains templates for LLM prompting
  - `full_match_prompt.md`: Prompt template for full string matching tasks
  - `partial_match_prompt.md`: Prompt template for partial string matching (substring extraction) tasks
- `run_llms.py`: Script to run LLM-based regex generation
- `run_synthesizers.py`: Script to run formal synthesizers (RFixer, FOREST)
- `run_reuse_by_example.md`: Documentation for running the reuse-by-example approach
- `requirements.txt`: Dependencies for running the scripts

## Running Different Strategies

### Reuse-by-example

To run the reuse-by-example strategy, you need to use the evaluator module. Refer to `run_reuse_by_example.md` for detailed instructions.

Example command:

```bash
cd evaluator
./gradlew :evaluation:run --args="manual-query --database <path to SQLite regex reuse database file> --output <path to output NDJSON file> <path to test suites file>"
```

### Formal Synthesizers

To run the formal synthesizers, use the `run_synthesizers.py` script. The script supports RFixer and FOREST.

```bash
python run_synthesizers.py --dataset <path to test suites file> --synthesizer <RFixer|FOREST|RFixer_GTP> --path-to-synthesizer <path to synthesizer executable> --output <path to output file> --mode <full_match|partial_match> --timeout <timeout in seconds>
```

Example command:

```bash
# Run RFixer for full match tasks
python run_synthesizers.py --dataset ../../data/regex-composition-bench/oss/full-match/full_match.ndjson --synthesizer RFixer --path-to-synthesizer /path/to/rfixer.jar --output ../../data/generated-regexes/synthesizers/rfixer/full-match/full_match.ndjson --mode full_match --timeout 120

# Run FOREST for partial match tasks
python run_synthesizers.py --dataset ../../data/regex-composition-bench/oss/partial-match/partial_match.ndjson --synthesizer FOREST --path-to-synthesizer /path/to/forest.py --output ../../data/generated-regexes/synthesizers/forest/partial-match/partial_match.ndjson --mode partial_match --timeout 120
```

### Large Language Models (LLMs)

To run LLM-based regex generation, use the `run_llms.py` script. The script supports both local LLMs (via Ollama) and proprietary models (via OpenAI API).

```bash
python run_llms.py --input <path to test suites file> --output <path to output file> --mode <full_match|partial_match> --api-type <ollama|openai> --model <model name> [--url <API URL>] [--openai-api-key <API key>] [--temperature <temperature>] [--attempts <max attempts>] [--timeout <timeout in seconds>] [--output-trials]
```

Example commands:

```bash
# Using local model via Ollama
python run_llms.py --input ../../data/regex-composition-bench/oss/full-match/full_match.ndjson --output ../../data/generated-regexes/llms/llama3/full-match/full_match.ndjson --mode full_match --api-type ollama --model mistral:latest --url http://localhost:11434/api/chat --temperature 0 --attempts 3 --timeout 120

# Using OpenAI model
python run_llms.py --input ../../data/regex-composition-bench/oss/partial-match/partial_match.ndjson --output ../../data/generated-regexes/llms/o3-mini/partial-match/partial_match.ndjson --mode partial_match --api-type openai --model o3-mini --openai-api-key YOUR_API_KEY --temperature 0 --attempts 3 --timeout 120
```

## LLM Prompting Strategy

The LLM approach uses carefully crafted prompts (in the `prompts/` directory) to generate three different types of regexes for each task:

1. **Conservative**: A strict regex that matches only the given positive examples
2. **Liberal**: A more generalized regex that captures broader patterns
3. **Balanced**: A regex that strikes a balance between conservatism and liberalism

This multi-faceted approach allows for better evaluation of how well LLMs can capture the intended constraints.

## Requirements

Install dependencies with:

```bash
pip install -r requirements.txt
```

For synthesizers, refer to their respective repositories for installation instructions:
- [RFixer](https://github.com/rongpan/RFixer)
- [FOREST](https://github.com/Marghrid/FOREST)
