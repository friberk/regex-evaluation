#!/usr/bin/env python3
from contextlib import contextmanager
import os.path
import io
import multiprocessing as mp
import ujson as json
import re
import numpy as np
from pathlib import Path
import time
from signal import signal, alarm, SIGALRM
import sys
sys.path.append(os.path.abspath(os.path.pardir))
from helpfulness_score.helpfulness_score import calculate_helpfulness_score

BEST_TARGETS = {
    "reuse-by-example": ["../../data/generated-regexes-with-semantic-similarities/reuse-by-example/full-match/full_match.ndjson", "../../data/generated-regexes-with-semantic-similarities/reuse-by-example/partial-match/partial_match.ndjson"],
    "rfixer": ["../../data/generated-regexes-with-semantic-similarities/synthesizers/rfixer/full-match/full_match.ndjson", "../../data/regex-reuse/generated-regexes-with-semantic-similarities/synthesizers/rfixer/partial-match/partial_match.ndjson"],
    "o3-mini": ["../../data/generated-regexes-with-semantic-similarities/llms/o3-mini/full-match/full_match.ndjson", "../../data/regex-reuse/generated-regexes-with-semantic-similarities/llms/o3-mini/partial-match/partial_match.ndjson"]
}

# Configuration
BASE_DIR = "../../data"
INPUT_DIR = f"{BASE_DIR}/generated-regexes-with-semantic-similarities"
OUTPUT_DIR = f"{BASE_DIR}/generated-regexes-with-helpfulness-scores"
n_chunks = mp.cpu_count()
KEEP_SAME_PROJECT_REGEXES = False

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Regex with timeouts
@contextmanager
def timeout(seconds):
    def handler(signum, frame):
        raise TimeoutError('Regex operation timed out.')

    signal(SIGALRM, handler)
    alarm(seconds)
    try:
        yield
    finally:
        alarm(0)

def exec_helpfulness_score_with_timeout(candidate_regex, positive_examples, negative_examples, timeout_seconds=10):
    """Execute helpfulness score calculation with timeout"""
    try:
        with timeout(timeout_seconds):
            return calculate_helpfulness_score(candidate_regex, positive_examples, negative_examples)
    except TimeoutError:
        raise TimeoutError('Semantic similarity calculation timed out.')

def find_all_ndjson_files(input_dir):
    """Find all ndjson files in the input directory."""
    all_files = []

    if not os.path.exists(input_dir):
        print(f"Input directory {input_dir} does not exist")
        return all_files

    # Walk through all files in the input directory
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith(".ndjson") and not "_trial" in file:
                # flatten the values in the BEST_TARGETS dictionary
                best_targets_paths = []
                for key, value in BEST_TARGETS.items():
                    best_targets_paths.extend(value)


                filepath = os.path.join(root, file)

                if not (filepath in best_targets_paths):
                    continue

                # Determine category and match_type from path
                rel_path = os.path.relpath(root, input_dir)
                path_parts = rel_path.split(os.path.sep)

                if len(path_parts) >= 1:
                    category = path_parts[0]
                    if category in ["reuse-by-example", "synthesizers", "llms"]:
                        # Determine subcategory and match_type based on path depth
                        if len(path_parts) >= 3 and category != "reuse-by-example":
                            subcategory = path_parts[1]
                            match_type = path_parts[2]
                        elif len(path_parts) >= 2:
                            subcategory = None
                            match_type = path_parts[1]
                        else:
                            # Skip files that don't match expected structure
                            continue

                        # Only process full-match and partial-match directories
                        if match_type in ["full-match", "partial-match"]:
                            all_files.append((filepath, category, subcategory, match_type))

    return all_files

def find_newline_pos(f, n):
    """Find the position of the nearest newline before position n."""
    f.seek(n)
    c = f.read(1)
    while c != '\n' and n > 0:
        n -= 1
        f.seek(n)
        c = f.read(1)
    return n

def prestart(filename):
    """Prepare the file chunks for parallel processing."""
    fsize = os.path.getsize(filename)
    if fsize == 0:
        return []

    initial_chunks = list(range(0, fsize, int(fsize/n_chunks)))[:-1]
    f = io.open(filename, 'r', encoding='utf-8')
    pieces = sorted(set([find_newline_pos(f, n) for n in initial_chunks]))
    pieces.append(fsize)
    f.close()

    args = zip([x+1 if x > 0 else x for x in pieces], [x for x in pieces[1:]])
    return list(args)

def process_worker(filename, start, end, category, subcategory, match_type):
    # Create the same directory structure in output
    rel_path = os.path.relpath(os.path.dirname(filename), INPUT_DIR)
    output_dir = os.path.join(OUTPUT_DIR, rel_path)
    # output_dir = os.path.join(OUTPUT_DIR, category, match_type)
    os.makedirs(output_dir, exist_ok=True)

    # Use the same filename for output
    output_filename = os.path.join(output_dir, os.path.basename(filename))

    # Create a lock for this output file to prevent concurrent writes
    file_lock = mp.Lock()

    f = io.open(filename, 'r', encoding='utf-8')
    f.seek(start)

    # Collect processed entries for this chunk
    processed_entries = []

    total_len = 0
    for line in f:
        try:
            entry = json.loads(line)

            candidates = entry["candidates"]
            positive_examples = []
            negative_examples = []

            for test_string in entry["strings"]:
                if match_type == "full-match":
                    if test_string["full_match"]:
                        positive_examples.append(test_string["matched_string"])
                    else:
                        negative_examples.append(test_string["string"])
                elif match_type == "partial-match":
                    if test_string["partial_match"]:
                        positive_examples.append(test_string["matched_string"])
                    else:
                        negative_examples.append(test_string["string"])

            # Calculate syntactic similarity for each candidate
            candidates_with_helpfulness_scores = []

            for candidate in candidates:
                regex = candidate.get("regex_pattern") or candidate.get("regex", "")

                if not regex:
                    helpfulness_score = None
                else:
                    try:
                        res = exec_helpfulness_score_with_timeout(regex, positive_examples, negative_examples)
                        helpfulness_score = round(res, 4)
                    except Exception as e:
                        print(f"Error while calculating helpfulness score: {e}")
                        helpfulness_score = None

                candidate["helpfulness_score"] = helpfulness_score

                candidates_with_helpfulness_scores.append(candidate)

            entry["candidates"] = candidates_with_helpfulness_scores

            # Now calculate for the ground truth regex
            ground_truth = entry.get("regex_pattern") or entry.get("regex", "")

            if not ground_truth:
                gt_helpfulness_score = None
            else:
                try:
                    res = exec_helpfulness_score_with_timeout(ground_truth, positive_examples, negative_examples)
                    gt_helpfulness_score = round(res, 4)
                except Exception as e:
                    print(f"Error while calculating helpfulness score for ground truth: {e}")
                    gt_helpfulness_score = None

            entry["helpfulness_score"] = gt_helpfulness_score

            processed_entries.append(entry)

        except Exception as e:
            print(f"Error processing line: {e}")

        total_len += len(line)
        if (total_len + start) >= end:
            break

    f.close()

    # Write all processed entries to the output NDJSON file
    with file_lock:
        with open(output_filename, 'a') as out_f:
            for entry in processed_entries:
                json_line = json.dumps(entry)
                out_f.write(json_line + '\n')

def process_file(file_info):
    """Process a single file with parallel chunks."""
    filename, category, subcategory, match_type = file_info
    print(f"Processing {filename}")

    # Create output directory (preserving directory structure)
    rel_path = os.path.relpath(os.path.dirname(filename), INPUT_DIR)
    output_dir = os.path.join(OUTPUT_DIR, rel_path)
    os.makedirs(output_dir, exist_ok=True)

    # Clear the output file if it exists (start fresh)
    output_filename = os.path.join(output_dir, os.path.basename(filename))
    if os.path.exists(output_filename):
        os.remove(output_filename)

    # Split file into chunks
    chunks = prestart(filename)
    if not chunks:
        print(f"File {filename} is empty or doesn't exist")
        return

    # Create and start workers for each chunk
    # if category == "reuse-by-example":
    #     worker_func = process_reuse_by_example_worker
    # elif category == "synthesizers":
    #     worker_func = process_synthesizers_worker
    # else:
    #     worker_func = process_llms_worker

    print("Processing {} with {} chunks".format(filename, len(chunks)))

    worker_func = process_worker

    workers = [
        mp.Process(
            target=worker_func,
            args=(filename, start, end, category, subcategory, match_type)
        )
        for start, end in chunks
    ]

    # Start all workers
    for worker in workers:
        worker.start()

    # Wait for all workers to complete
    for worker in workers:
        worker.join()

    print(f"Completed processing {filename}")

def main():
    start_time = time.time()
    print(f"Starting parallel processing with {n_chunks} processes per file")
    print(f"{mp.cpu_count()} CPUs available")
    # Find all ndjson files to process
    all_files = find_all_ndjson_files(INPUT_DIR)
    print(all_files)
    # exit()
    print(f"Found {len(all_files)} files to process")

    # Process files one by one (could be parallelized further if needed)
    for file_info in all_files:
        process_file(file_info)

    end_time = time.time()
    print(f"All processing completed in {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    main()