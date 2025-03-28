import ndjson
import argparse
import subprocess
import json
import tempfile
from tqdm.auto import tqdm
import time
import re
import random
random.seed(42)

def run_rfixer(data, path_to_synthesizer, mode, timeout, output, gtp=False):
    # Run RFixer on the dataset
    """
    RFixer needs an input file with the following format:
    .
    +++
    Positive examples, one per line
    ---
    Negative examples, one per line
    """

    main_pbar = tqdm(total=len(data), desc='Running RFixer')
    rfixer_sol_regex = re.compile(r'\#sol\#(.*)\#sol\#')

    with open(output, 'a') as f:
        for i, task in enumerate(data):
            positive_examples = []
            negative_examples = []
            if mode == 'full_match':
                for string in task["strings"]:
                    if string["full_match"]:
                        positive_examples.append(string["string"])
                    else:
                        negative_examples.append(string["string"])
            elif mode == 'partial_match':
                for string in task["strings"]:
                    if string["partial_match"]:
                        positive_examples.append(string["matched_string"])
                    else:
                        negative_examples.append(string["string"])

            main_pbar.set_description(f'Synthesizing regex for composition task {i + 1}/{len(data)}')

            if not gtp:
                EMPTY_GROUND_TRUTH = '.'
            else:
                EMPTY_GROUND_TRUTH = random.choice(positive_examples) if len(positive_examples) > 0 else '.'

            # Create a temporary file for the actual run
            with tempfile.NamedTemporaryFile(mode='w', delete=True) as temp_file:
                temp_file.write(EMPTY_GROUND_TRUTH + '\n')
                temp_file.write('+++\n')
                for example in positive_examples:
                    temp_file.write(example + '\n')
                temp_file.write('---\n')
                for example in negative_examples:
                    temp_file.write(example + '\n')

                # Make sure the data is written to the file
                temp_file.flush()

                start_time = time.time()

                # Run RFixer using the temporary file
                command = f'java -jar {path_to_synthesizer} -m 1 fix --file {temp_file.name}'
                cwd = "/".join(path_to_synthesizer.split('/')[:-1])
                ld_export = cwd if not "/target" in cwd else cwd + "/.."
                try:
                    # For debug print the command
                    # print(command)
                    # print("/".join(path_to_synthesizer.split('/')[:-1]))

                    # From command remove the file name and CD to the directory
                    cmd_output = subprocess.check_output(
                        f"export LD_LIBRARY_PATH={ld_export} && {command}",
                        shell=True,
                        cwd=cwd,
                        timeout=timeout
                    ).decode('utf-8')
                    print(cmd_output)
                    status = "SUCCESS"
                except subprocess.TimeoutExpired:
                    # Handle timeout case
                    status = "TIMEOUT"
                    cmd_output = ""
                    print(f"Process timed out after 120 seconds")
                except subprocess.CalledProcessError as e:
                    status = "FAILED"
                    print(e)

            elapsed_time = (time.time() - start_time) * 1000  # Convert to milliseconds

            # Parse the output
            if status != "FAILED" and status != "TIMEOUT":
                # Parse this part of the output: "solution is #sol#<regex>#sol#"
                parsed_regex = rfixer_sol_regex.search(cmd_output)
                sol_found = bool(parsed_regex)

                if sol_found:
                    parsed_regex = parsed_regex.group(1)
                    status = "SUCCESS"
                else:
                    parsed_regex = 'Solution not found!'
                    status = "SOLUTION_NOT_FOUND"

            if status != "FAILED" and status != "TIMEOUT":
                if parsed_regex == 'Solution not found!':
                    candidate_regex = None
                else:
                    candidate_regex = parsed_regex

            output_dict = {
                'regex_id': task['regex_id'],
                'project_id': task['project_id'],
                'test_suite_id': task['test_suite_id'],
                'regex_pattern': task['regex_pattern'],
                'strings': task['strings'],
                'candidates': [] if (status == "FAILED" or status == "SOLUTION_NOT_FOUND" or status == "TIMEOUT") else [candidate_regex],
                'test_string_count': task ['test_string_count'],
                'elapsed_time': elapsed_time,
                'status': status
            }

            # Write to output file
            f.write(json.dumps(output_dict) + '\n')
            f.flush()  # Ensure it's written in case of interruption

            main_pbar.update(1)

    main_pbar.close()

def run_forest(data, path_to_synthesizer, mode, timeout, output):
    # Run Forest on the dataset
    """
    FOREST needs an input file with the following format:
    ++
    Positive examples, one per line
    --
    Negative examples, one per line
    """

    main_pbar = tqdm(total=len(data), desc='Running FOREST')


    with open(output, 'a') as f:
        for i, task in enumerate(data):
            positive_examples = []
            negative_examples = []
            if mode == 'full_match':
                for string in task["strings"]:
                    if string["full_match"]:
                        positive_examples.append(string["string"])
                    else:
                        negative_examples.append(string["string"])
            elif mode == 'partial_match':
                for string in task["strings"]:
                    if string["partial_match"]:
                        positive_examples.append(string["matched_string"])
                    else:
                        negative_examples.append(string["string"])

            main_pbar.set_description(f'Synthesizing regex for composition task {i + 1}/{len(data)}')

            # Create a temporary file for the actual run
            with tempfile.NamedTemporaryFile(mode='w', delete=True) as temp_file:
                temp_file.write('++\n')
                for example in positive_examples:
                    temp_file.write(example + '\n')
                temp_file.write('--\n')
                for example in negative_examples:
                    temp_file.write(example + '\n')

                # Make sure the data is written to the file
                temp_file.flush()

                start_time = time.time()

                # Run FOREST using the temporary file
                command = f'python3 {path_to_synthesizer.split("/")[-1]} --no-disambiguation -v {temp_file.name}'
                try:
                    # For debug print the command
                    # print(command)
                    # print("/".join(path_to_synthesizer.split('/')[:-1]))

                    # From command remove the file name and CD to the directory
                    cmd_output = subprocess.check_output(
                        command,
                        shell=True,
                        cwd="/".join(path_to_synthesizer.split('/')[:-1]),
                        timeout=timeout  # Add 120 second timeout
                    ).decode('utf-8')
                    print(cmd_output)
                    status = "SUCCESS"
                except subprocess.TimeoutExpired:
                    # Handle timeout case
                    status = "TIMEOUT"
                    cmd_output = ""
                    print(f"Process timed out after 120 seconds")
                except subprocess.CalledProcessError as e:
                    status = "FAILED"
                    print(e)

            elapsed_time = (time.time() - start_time) * 1000  # Convert to milliseconds

            # Parse the output
            if status != "FAILED" and status != "TIMEOUT":
                if 'Solution not found!' in cmd_output:
                    parsed_regex = 'Solution not found!'
                    status = "SOLUTION_NOT_FOUND"
                else:
                    parsed_regex = cmd_output.split('Solution:\n')[1].split('\n')[0][2:]
                    status = "SUCCESS"

            if status != "FAILED" and status != "TIMEOUT":
                if parsed_regex == 'Solution not found!':
                    candidate_regex = None
                else:
                    candidate_regex = parsed_regex

            output_dict = {
                'regex_id': task['regex_id'],
                'project_id': task['project_id'],
                'test_suite_id': task['test_suite_id'],
                'regex_pattern': task['regex_pattern'],
                'strings': task['strings'],
                'candidates': [] if (status == "FAILED" or status == "SOLUTION_NOT_FOUND" or status == "TIMEOUT") else [candidate_regex],
                'test_string_count': task ['test_string_count'],
                'elapsed_time': elapsed_time,
                'status': status
            }

            # Write to output file
            f.write(json.dumps(output_dict) + '\n')
            f.flush()  # Ensure it's written in case of interruption

            main_pbar.update(1)

    main_pbar.close()

def main():
    # Argument parser
    parser = argparse.ArgumentParser(description='Run synthesizers on a dataset')
    parser.add_argument('--dataset', type=str, help='Path to the dataset', required=True)
    parser.add_argument('--synthesizer', type=str, help='Name of the synthesizer to run', required=True, choices=['AlphaRegex', 'FOREST', 'RFixer', 'RFixer_GTP'])
    parser.add_argument('--path-to-synthesizer', type=str, help='Path to the synthesizer executable', required=True)
    parser.add_argument('--output', type=str, help='Path to the output file', required=True)
    parser.add_argument('--mode', type=str, help='Regex match mode', choices=['full_match', 'partial_match'], default='full_match')
    parser.add_argument('--timeout', type=int, help='Timeout for each run', default=120)
    args = parser.parse_args()

    # Load the dataset
    with open(args.dataset) as f:
        data = ndjson.load(f)

    if args.synthesizer == 'FOREST':
        run_forest(data, args.path_to_synthesizer, args.mode, args.timeout, args.output)
    elif args.synthesizer == 'RFixer':
        run_rfixer(data, args.path_to_synthesizer, args.mode, args.timeout, args.output, gtp=False)
    elif args.synthesizer == 'RFixer_GTP':
        run_rfixer(data, args.path_to_synthesizer, args.mode, args.timeout, args.output, gtp=True)

if __name__ == '__main__':
    main()