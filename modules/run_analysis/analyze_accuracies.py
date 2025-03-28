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

# Configuration
BASE_DIR = "../../data"
INPUT_DIR = f"{BASE_DIR}/generated-regexes"
OUTPUT_DIR = f"{BASE_DIR}/generated-regexes-with-accuracies"
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

def exec_regex_with_timeout(regex, string, mode, timeout_seconds=10):
    """Execute a regex with a timeout."""
    try:
        with timeout(timeout_seconds):
            if mode == "full_match":
                match = re.fullmatch(regex, string)
            else:
                match = re.search(regex, string)
            return match
    except TimeoutError:
        raise TimeoutError('Regex operation timed out.')

def calculate_regex_accuracy(regex, test_strings, mode):
    """Test a regex pattern against test strings and return the accuracy."""
    correct_decisions = 0
    total_decisions = 0

    try:
        pattern = re.compile(regex)

        for test_string in test_strings:
            string = test_string["string"]

            if mode == "full_match":
                # Full match mode
                try:
                    match = exec_regex_with_timeout(pattern, string, "full_match")
                    actual = bool(match)
                except TimeoutError:
                    # Timeout
                    total_decisions += 1
                    continue

                if test_string["full_match"] and not actual:
                    total_decisions += 1
                elif not test_string["full_match"] and actual:
                    total_decisions += 1
                elif test_string["full_match"] and actual:
                    # No failures
                    correct_decisions += 1
                    total_decisions += 1
                elif not test_string["full_match"] and not actual:
                    # No failures
                    correct_decisions += 1
                    total_decisions += 1
            else:
                # Partial match mode
                try:
                    match = exec_regex_with_timeout(pattern, string, "partial_match")
                    actual = bool(match)
                except TimeoutError:
                    # Timeout
                    total_decisions += 1
                    continue

                if test_string["partial_match"] and not actual:
                    total_decisions += 1
                elif not test_string["partial_match"] and actual:
                    total_decisions += 1
                elif test_string["partial_match"] and actual:
                    # Check if the matched substring is correct
                    matched_string = match.group(0)
                    expected_match = test_string["matched_string"]

                    if matched_string != expected_match:
                        total_decisions += 1
                    else:
                        # No failures
                        correct_decisions += 1
                        total_decisions += 1
                elif not test_string["partial_match"] and not actual:
                    # No failures
                    correct_decisions += 1
                    total_decisions += 1

        # Return the accuracy in .4f format
        if total_decisions > 0:
            return round(correct_decisions / total_decisions, 4)
        else:
            return 0.0
    except re.error:
        # Regex failed to compile in Python
        return 0.0
    except Exception:
        # Other exceptions
        return 0.0

def sample_reuse_by_example_candidates(ground_truth_regex_id, ground_truth_project_id, candidates, seed):
    """
    Reuse by example returns 1000s of candidates for each case.
    Sample 1 candidate for each edge coverage decile.
    """
    # Set random seed for reproducibility
    np.random.seed(seed)

    # Remove the ground truth regex from the candidates and optionally from the same project
    candidates = [
        candidate for candidate in candidates
        if candidate["regex_id"] != ground_truth_regex_id and
        (KEEP_SAME_PROJECT_REGEXES or candidate["project_id"] != ground_truth_project_id)
    ]

    # Group candidates into deciles based on edge coverage (0-0.1, 0.1-0.2, ..., 0.9-1.0)
    deciles = [[] for _ in range(10)]

    for candidate in candidates:
        edge_coverage = candidate["full_coverage_summary"]["edgeCoverage"]
        # Calculate decile index (0-9) and ensure 1.0 goes to the 9th decile
        decile_idx = min(int(edge_coverage * 10), 9)
        deciles[decile_idx].append(candidate)

    # Sample 1 candidate from each decile if candidates exist
    sampled_candidates = []
    for decile in deciles:
        if decile:
            # Randomly select one candidate from this decile
            idx = np.random.randint(0, len(decile))
            sampled_candidates.append(decile[idx])

    return sampled_candidates

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
                filepath = os.path.join(root, file)

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

def process_reuse_by_example_worker(filename, start, end, category, subcategory, match_type):
    """Process a chunk of a reuse-by-example file."""
    mode = "full_match" if match_type == "full-match" else "partial_match"

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

            # Process entry
            test_strings = entry["strings"]
            candidates = entry["candidates"]

            # Sample candidates
            sampled_candidates = sample_reuse_by_example_candidates(
                entry["regex_id"],
                entry["project_id"],
                candidates,
                42
            )

            # Calculate accuracy for each candidate
            candidates_with_accuracies = []

            if len(sampled_candidates) == 0:
                candidates_with_accuracies.append({
                    "regex_pattern": "",
                    "accuracy": None
                })

            for candidate in sampled_candidates:
                regex = candidate["regex_pattern"]
                accuracy = calculate_regex_accuracy(regex, test_strings, mode)
                candidate["accuracy"] = accuracy
                candidates_with_accuracies.append(candidate)

            # Update entry with processed candidates
            entry["candidates"] = candidates_with_accuracies

            # Add to processed entries
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

def process_synthesizers_worker(filename, start, end, category, subcategory, match_type):
    """Process a chunk of a synthesizer file."""
    mode = "full_match" if match_type == "full-match" else "partial_match"

    # Create the same directory structure in output
    rel_path = os.path.relpath(os.path.dirname(filename), INPUT_DIR)
    output_dir = os.path.join(OUTPUT_DIR, rel_path)
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

            # Process entry
            test_strings = entry["strings"]
            candidates = entry["candidates"]

            # Calculate accuracy for each candidate
            candidates_with_accuracies = []

            if len(candidates) == 0:
                candidates_with_accuracies.append({
                    "regex_pattern": "",
                    "accuracy": None
                })

            for candidate in candidates:
                regex = candidates[0]

                accuracy = calculate_regex_accuracy(regex, test_strings, mode)

                candidates_with_accuracies.append({
                    "regex_pattern": regex,
                    "accuracy": accuracy
                })

                candidates_with_accuracies.append(candidate)

            # Fix a weird bug where the first candidate is duplicated
            if len(candidates_with_accuracies) > 1:
                if isinstance(candidates_with_accuracies[1], str):
                    # Remove the string candidate
                    candidates_with_accuracies = candidates_with_accuracies[0:1]

            # Update entry with processed candidates
            entry["candidates"] = candidates_with_accuracies

            # Add to processed entries
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

def process_llms_worker(filename, start, end, category, subcategory, match_type):
    """Process a chunk of a LLMs file."""
    mode = "full_match" if match_type == "full-match" else "partial_match"

    # Create the same directory structure in output
    rel_path = os.path.relpath(os.path.dirname(filename), INPUT_DIR)
    output_dir = os.path.join(OUTPUT_DIR, rel_path)
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

            # Process entry
            test_strings = entry["strings"]
            candidates = entry["candidates"]

            # Calculate accuracy for each candidate
            candidates_with_accuracies = []

            for candidate in candidates:
                regex = candidate["regex"]

                if not regex:
                    accuracy = None
                else:
                    accuracy = calculate_regex_accuracy(regex, test_strings, mode)

                candidate["accuracy"] = accuracy

                candidates_with_accuracies.append(candidate)

            # Update entry with processed candidates
            entry["candidates"] = candidates_with_accuracies

            # Add to processed entries
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
    if category == "reuse-by-example":
        worker_func = process_reuse_by_example_worker
    elif category == "synthesizers":
        worker_func = process_synthesizers_worker
    else:
        worker_func = process_llms_worker

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
    # print(all_files)
    # exit()
    print(f"Found {len(all_files)} files to process")

    # Process files one by one (could be parallelized further if needed)
    for file_info in all_files:
        process_file(file_info)

    end_time = time.time()
    print(f"All processing completed in {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    main()