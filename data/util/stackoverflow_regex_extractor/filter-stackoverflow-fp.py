import argparse
import asyncio
from functools import partial
import json
import logging
import os
import re
import sys
from time import sleep
from typing import List, Dict, Any, NamedTuple
from fast_ndjson_processor import FastNDJSONProcessor, FastNDJSONWriter
import orjson
from openai import OpenAI
import tempfile

SYSTEM_PROMPT = """
You are a regex expert tasked with classifying patterns extracted from Stack Overflow posts. Your script collected content from <code> tags, but also captured non-regex content. Your job is to classify these patterns and extract actual regex when needed.

TASK
Analyze a given pattern and determine if it is:
- VALID: A standalone regex pattern ready for use
- INVALID: Not a regex pattern at all
- PARTIALLY VALID: Contains a valid regex embedded within other code/text

INPUT
You will receive a JSON object:
{
  "pattern": "..."
}

RETURN
Output a JSON object:
{
  "validity": "VALID" | "INVALID" | "PARTIALLY VALID",
  "extracted_regex": null | "extracted_regex_here"
}

DECISION RULES

VALID
A pattern is VALID when it:
- Is a complete, standalone regex pattern that is similar to what developers might use in their code
- Contains regex metacharacters or syntax (*, +, ?, [], {}, (), |, ^, $, \d, \w, \s, etc.)
- Could be directly used in a regex function without modification
- May or may not include delimiters (/, ~, etc.) depending on the language context

INVALID
A pattern is INVALID when it:
- Contains no regex syntax whatsoever
- Is plain text, code, or commands without regex patterns
- Is a file path, URL, or identifier without regex metacharacters
- Is HTML, XML, JSON, or other structured data without regex patterns
- Is a placeholder or variable name like `$regex` or `{pattern}`

PARTIALLY VALID
A pattern is PARTIALLY VALID when it contains a valid regex but is embedded in:
- Function calls: re.compile(...), preg_match(...), String.match(...)
- Variable assignments: pattern = "..."
- Command-line arguments: grep -E '...'
- String delimiters that need removal: quotes, slashes with flags
- Code comments or documentation

EXTRACTION RULES FOR PARTIALLY VALID

When extracting regex from PARTIALLY VALID patterns:
1. Remove surrounding function calls and parameters
2. Remove variable assignment syntax
3. Remove command-line tool names and flags
4. Remove string delimiters (quotes) but preserve regex delimiters if they're part of the pattern
5. For JavaScript/Perl style /pattern/flags, extract just the pattern without delimiters and flags
6. Preserve escape sequences that are part of the regex pattern

EXAMPLES

EXAMPLE 1 - INVALID

INPUT:
{
  "pattern": "git clone git://core.git.wordpress.org/"
}

ANALYSIS: This is a git command with a URL, containing no regex syntax.

RETURN:
{
  "validity": "INVALID",
  "extracted_regex": null
}

EXAMPLE 2 - VALID

INPUT:
{
  "pattern": "(?<file_name>\\w*\\.\\w*)"
}

ANALYSIS: This is a complete regex pattern with a named capture group for matching filenames.

RETURN:
{
  "validity": "VALID",
  "extracted_regex": null
}

EXAMPLE 3 - PARTIALLY VALID

INPUT:
{
  "pattern": "egrep -o '[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}'"
}

ANALYSIS: Contains a valid IP address regex as an argument to egrep command.

RETURN:
{
  "validity": "PARTIALLY VALID",
  "extracted_regex": "[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}"
}

EXAMPLE 4 - PARTIALLY VALID

INPUT:
{
  "pattern": "String.replace(/(<pre[\\s\\S]*?>[\\s\\S]*?<\\/pre>)|[ \\t]{2,}|\\n/g, '$1');"
}

ANALYSIS: Contains a JavaScript regex within a replace method call.

RETURN:
{
  "validity": "PARTIALLY VALID",
  "extracted_regex": "(<pre[\\s\\S]*?>[\\s\\S]*?<\\/pre>)|[ \\t]{2,}|\\n"
}

EXAMPLE 5 - PARTIALLY VALID

INPUT:
{
  "pattern": "regex = \"^((?!-)[A-Za-z0-9-]{1,63}(?<!-)\\\\.).+[A-Za-z]{2,6}$\""
}

ANALYSIS: Contains a domain validation regex assigned to a variable.

RETURN:
{
  "validity": "PARTIALLY VALID",
  "extracted_regex": "^((?!-)[A-Za-z0-9-]{1,63}(?<!-)\\\\.).+[A-Za-z]{2,6}$"
}

EXAMPLE 6 - VALID

INPUT:
{
  "pattern": "/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$/"
}

ANALYSIS: A complete email validation regex with JavaScript-style delimiters.

RETURN:
{
  "validity": "VALID",
  "extracted_regex": null
}

EXAMPLE 7 - INVALID

INPUT:
{
  "pattern": "/usr/local/bin/python3"
}

ANALYSIS: A file system path with no regex syntax.

RETURN:
{
  "validity": "INVALID",
  "extracted_regex": null
}

EXAMPLE 8 - PARTIALLY VALID

INPUT:
{
  "pattern": "re.findall(r'\\b\\d{3}-\\d{2}-\\d{4}\\b', text)"
}

ANALYSIS: Contains a SSN-matching regex within a Python re.findall call.

RETURN:
{
  "validity": "PARTIALLY VALID",
  "extracted_regex": "\\b\\d{3}-\\d{2}-\\d{4}\\b"
}

INSTRUCTIONS

1. Check for regex syntax first: Look for metacharacters (*, +, ?, [], {}, (), |, ^, $, \, etc.)
2. If no regex syntax found: Mark as INVALID
3. If regex syntax found:
   - Is it standalone? -> VALID
   - Is it embedded in code? -> PARTIALLY VALID, extract the regex
4. For edge cases:
   - Simple strings with only dots (.) or single backslashes might be INVALID unless other regex syntax is present
   - Paths starting with / are INVALID unless they contain clear regex patterns
   - Consider context: /pattern/ is likely a regex, /path/to/file is likely a path

SPECIAL CONSIDERATIONS

- Escaped characters: \\. in regex means literal dot, preserve the escaping
- Language differences: Some languages use raw strings (r"..."), others don't
- Delimiter variations: /.../, ~...~, m{...}, etc. are all valid regex delimiters
- Flags: Ignore flags (g, i, m, s, etc.) when extracting, focus on the pattern
- Quotes in patterns: If quotes are part of the regex pattern itself, preserve them

IMPORTANT NOTES

- Always return valid JSON
- For VALID patterns, extracted_regex is always null
- For INVALID patterns, extracted_regex is always null
- For PARTIALLY VALID patterns, extracted_regex must contain the extracted pattern
- Preserve the original escape sequences in the extracted regex
- Do not attempt to validate the regex syntax itself, focus on classification
"""

lookup_table = {}

def build_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Filter spammy rows from a NDJSON using OpenAI (incremental writes).")
    p.add_argument("--input-file", required=True, help="Path to input NDJSON")
    p.add_argument("--batch-id-file", required=False, default="./batchIds.txt", help="Path to write batch IDs for future retrieval or read from")
    p.add_argument("--output-file", required='filter' in sys.argv, help="Path to write filtered NDJSON")
    p.add_argument("--discarded-output-file", default=None, help="Optional path to write only discarded (false positive) rows")
    p.add_argument("--custom-id-prefix", default="so-post", help="Prefix for custom_id")
    p.add_argument("--model", default="gpt-5-nano", help="OpenAI model (default: gpt-5-nano)")
    p.add_argument("--n-workers", type=int, default=os.cpu_count(), help="Number of workers")
    p.add_argument("--n-batches", type=int, default=os.cpu_count() * 2, help="Number of batches to divide the input file into")
    p.add_argument("--max-tokens", type=int, default=3, help="Max tokens to generate")
    p.add_argument("--temperature", type=float, default=0, help="Temperature for OpenAI")
    p.add_argument("--seed", type=int, default=42, help="Seed for random number generator")
    p.add_argument("--reasoning-effort", type=str, default="low", help="Reasoning effort for OpenAI")
    p.add_argument("--verbosity", type=str, default="low", help="Verbosity level")
    p.add_argument("--mode", type=str, default="query", choices=["query", "filter"], help="Mode to run in. Query mode will only query the batches and write the batch IDs to the batch-id-file. Filter mode will filter the input file and write the filtered NDJSON to the output file, assuming the batches in batch-id-file have already been processed by the LLM.")
    return p.parse_args()

def make_messages(pattern: str) -> List[Dict[str, str]]:
    payload = {
        "pattern": pattern
    }

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": orjson.dumps(payload).decode("utf-8")}
    ]

def query_chunk_sync(chunk: List[dict], batch_info: NamedTuple, args_dict: dict):
    args = argparse.Namespace(**args_dict)

    client = OpenAI()

    batch_jsonl = []

    for record in chunk:
        for i, pattern in enumerate(record["patterns"]):
            messages = make_messages(pattern)
            if "#comment" in record["uri"]:
                comment_id = record["uri"].split("#comment")[1].split("_")[0]
            else:
                # It is not a comment
                if "/questions/" in record["uri"]:
                    comment_id = record["uri"].split("https://www.stackoverflow.com/questions/")[1]
                else:
                    comment_id = record["uri"].split("https://www.stackoverflow.com/a/")[1]

            custom_id = f"{args.custom_id_prefix}-{comment_id}"
            if i != 0:
                custom_id += f"-{i}"

            payload = {
                "custom_id": custom_id,
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": args.model,
                    "messages": messages,
                    "temperature": 1 if args.model.startswith("gpt-5") else args.temperature,
                    "reasoning_effort": args.reasoning_effort,
                    "verbosity": args.verbosity,
                    "seed": args.seed,
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "regex_extraction",
                            "strict": True,
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "validity": {"type": "string", "enum": ["VALID", "INVALID", "PARTIALLY VALID"]},
                                    "extracted_regex": {"type": ["string", "null"]}
                                },
                                "required": ["validity", "extracted_regex"],
                                "additionalProperties": False
                            }
                        }
                    }
                }
            }

            batch_jsonl.append(orjson.dumps(payload).decode("utf-8"))

    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl", mode="w", encoding="utf-8") as temp_file:
            temp_file.write("\n".join(batch_jsonl))
            temp_file_path = temp_file.name

        with open(temp_file_path, "rb") as file_obj:
            batch_input_file = client.files.create(
                file=file_obj,
                purpose="batch"
            )

        batch_input_file_id = batch_input_file.id
        batch = client.batches.create(
            input_file_id=batch_input_file_id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
            metadata={
                "description": f"{args.custom_id_prefix} regex extractor"
            }
        )

        print(f"Successfully created batch: {batch.id}")
        with open(args.batch_id_file, "a") as f:
            f.write(f"{batch.id}\n")
        return batch.id
    except Exception as e:
        print(f"Error creating batch: {str(e)}")
        return None
    finally:
        # Clean up the temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                print(f"Warning: Failed to delete temporary file {temp_file_path}: {str(e)}")

def build_lookup_table():
    client = OpenAI()
    TOTAL_LINE_READ = 0

    with open(args.batch_id_file, "r") as f:
        batch_ids = f.read().splitlines()

    for batch_id in batch_ids:
        batch = client.batches.retrieve(batch_id)
        output_file_id = batch.output_file_id

        if not output_file_id:
            print(f"Warning: No output file ID found for batch {batch_id}, skipping... It's probably still running.")
            print(f"Batch status: {batch.status}")
            print(f"Batch progress: {batch.request_counts}")
            continue

        result = client.files.content(output_file_id).content

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl", mode="wb") as temp_file:
            temp_file.write(result)

        with open(temp_file.name, "r") as file:
            for line in file:
                TOTAL_LINE_READ += 1
                json_object = orjson.loads(line.strip())
                content_str = json_object["response"]["body"]["choices"][0]["message"]["content"]
                try:
                    content_dict = orjson.loads(content_str)
                    lookup_table[json_object["custom_id"]] = content_dict
                except Exception as e:
                    print(f"Error parsing content: {e}")
                    print(f"Response: {json_object}")
                    print(f"Content: {content_str}")
                    print("Need manual intervention")
                    print("What should be the 'validity' and 'extracted_regex' for this entry?")
                    print("Enter the validity:")
                    validity = input()
                    print("Enter the extracted_regex:")
                    extracted_regex = input()
                    content_dict = {
                        "validity": validity,
                        "extracted_regex": None if (extracted_regex == "" or extracted_regex == "null" or extracted_regex == "None") else extracted_regex
                    }
                    lookup_table[json_object["custom_id"]] = content_dict

        os.unlink(temp_file.name)

    print(f"Built lookup table with {len(lookup_table)} entries")
    print(f"Read {TOTAL_LINE_READ} lines")

def filter_chunk_sync(chunk: List[dict], batch_info: NamedTuple, args_dict: dict):
    args = argparse.Namespace(**args_dict)
    filtered_count = 0
    discarded_count = 0
    for record in chunk:
        filtered_record = {
            "patterns": [],
            "type": "StackOverflowCommentRegexSource" if "#comment" in record["uri"] else "StackOverflowPostRegexSource",
            "uri": record["uri"],
            "uriAliases": record["uriAliases"],
        }

        discarded_record = {
            "patterns": [],
            "type": "StackOverflowCommentRegexSource" if "#comment" in record["uri"] else "StackOverflowPostRegexSource",
            "uri": record["uri"],
            "uriAliases": record["uriAliases"],
        }

        for i, pattern in enumerate(record["patterns"]):
            if "#comment" in record["uri"]:
                custom_id = args.custom_id_prefix + "-" + record["uri"].split("#comment")[1].split("_")[0]
            else:
                # It is not a comment
                if "/questions/" in record["uri"]:
                    custom_id = args.custom_id_prefix + "-" + record["uri"].split("https://www.stackoverflow.com/questions/")[1]
                else:
                    custom_id = args.custom_id_prefix + "-" + record["uri"].split("https://www.stackoverflow.com/a/")[1]
            if i != 0:
                custom_id += "-" + str(i)
            table_entry = lookup_table.get(custom_id)
            if table_entry is None:
                print(f"Warning: No entry found for custom_id: {custom_id}")
                continue
            if table_entry["validity"] == "VALID":
                filtered_count += 1
                filtered_record["patterns"].append(pattern)
            elif table_entry["validity"] == "PARTIALLY VALID":
                discarded_count += 1
                discarded_record["patterns"].append(pattern)
                if table_entry["extracted_regex"] is not None:
                    filtered_count += 1
                    filtered_record["patterns"].append(table_entry["extracted_regex"])
            elif table_entry["validity"] == "INVALID":
                discarded_count += 1
                discarded_record["patterns"].append(pattern)
            else:
                raise ValueError(f"Invalid validity: {table_entry['validity']}")

        if len(filtered_record["patterns"]) > 0:
            with open(args.output_file, "a") as f:
                f.write(orjson.dumps(filtered_record).decode("utf-8") + "\n")
        if args.discarded_output_file is not None:
            if len(discarded_record["patterns"]) > 0:
                with open(args.discarded_output_file, "a") as f:
                    f.write(orjson.dumps(discarded_record).decode("utf-8") + "\n")

    print(f"Wrote {filtered_count} regexes to {args.output_file}")
    if args.discarded_output_file is not None:
        print(f"Wrote {discarded_count} regexes to {args.discarded_output_file}")

if __name__ == "__main__":
    args = build_args()

    # Convert args to dict for multiprocessing (can't pickle Namespace directly)
    args_dict = vars(args)

    processor = FastNDJSONProcessor(n_workers=args.n_workers, show_progress=True, n_batches=args.n_batches)

    # Use a lambda to pass args_dict to the sync function
    if args.mode == "query":
        chunk_handler = partial(query_chunk_sync, args_dict=args_dict)
        processor.process_file_chunks(args.input_file, chunk_handler, return_results=False, include_batch_info=True)

        # ndjson_list = []
        # with open(args.input_file, "r") as f:
        #     for line in f:
        #         ndjson_list.append(orjson.loads(line))

        # query_chunk_sync(ndjson_list, args_dict)
    elif args.mode == "filter":
        build_lookup_table()
        # chunk_handler = partial(filter_chunk_sync, args_dict=args_dict)
        # processor.process_file_chunks(args.input_file, chunk_handler, return_results=False)

        ndjson_list = []
        with open(args.input_file, "r") as f:
            for line in f:
                ndjson_list.append(orjson.loads(line))

        filter_chunk_sync(ndjson_list, None, args_dict)
    else:
        raise ValueError(f"Invalid mode: {args.mode}")
