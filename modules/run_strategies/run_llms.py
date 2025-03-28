import json
import re
import time
import requests
import logging
import argparse
from contextlib import contextmanager
from pathlib import Path
from tqdm import tqdm

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@contextmanager
def timeout(seconds):
    from signal import signal, alarm, SIGALRM
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

def read_input_file(file_path):
    """Read the input file and yield each NDJSON row."""
    with open(file_path, 'r') as f:
        for line in f:
            if line.strip():  # Skip empty lines
                yield json.loads(line)

def prepare_full_match_prompt(test_strings, prompt_path):
    """Prepare the prompt for full match mode."""
    positive_strings = [s['string'] for s in test_strings if s['full_match'] == 1]
    negative_strings = [s['string'] for s in test_strings if s['full_match'] == 0]

    prompt_path = Path(prompt_path) / "full_match_prompt.md"
    with open(prompt_path, 'r') as f:
        prompt_template = f.read()

    positive_strings_formatted = "[" + ", ".join([f'"{s}"' for s in positive_strings]) + "]"
    negative_strings_formatted = "[" + ", ".join([f'"{s}"' for s in negative_strings]) + "]"

    # Replace placeholders in the template
    prompt = prompt_template.replace('{positive_strings}', positive_strings_formatted)
    prompt = prompt.replace('{negative_strings}', negative_strings_formatted)

    return prompt

def prepare_partial_match_prompt(test_strings, prompt_path):
    """Prepare the prompt for partial match mode."""
    positive_examples = []
    for s in test_strings:
        if s['partial_match'] == 1 and s['matched_string']:
            positive_examples.append(f"'{s['matched_string']}' in '{s['string']}'")

    negative_strings = [s['string'] for s in test_strings if s['partial_match'] == 0]

    prompt_path = Path(prompt_path) / "partial_match_prompt.md"
    with open(prompt_path, 'r') as f:
        prompt_template = f.read()

    negative_strings_formatted = "[" + ", ".join([f'"{s}"' for s in negative_strings]) + "]"

    # First we'll prepare a comma-separated list for sentence context
    matched_substrings_list = ", ".join(positive_examples)

    # Then we'll prepare a list-style format with each example on a new line
    matched_substrings_bullets = ""
    for example in positive_examples:
        matched_substrings_bullets += f"- {example}\n"

    # Then we'll prepare a list-style format with each example on a new line
    matched_substrings_bullets = ""
    for example in positive_examples:
        matched_substrings_bullets += f"- {example}\n"

    # Replace placeholders in the template
    prompt = prompt_template.replace('{negative_strings}', negative_strings_formatted)
    prompt = prompt.replace('{first_matched_substring_1} in {test_string_1}, ...', matched_substrings_list, 1)
    prompt = prompt.replace('{first_matched_substring_1} in {test_string_1}, ...', matched_substrings_bullets, 1)

    return prompt

def query_ollama(conversation_history, url, model, temperature=0, timeout=120):
    """Query the Ollama API with the given conversation history."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer sk-4b46b7c4080d49b3a415a67693db5947"
    }

    messages = []
    for i, content in enumerate(conversation_history):
        if i % 2 == 0:
            messages.append({"role": "user", "content": content})
        else:
            messages.append({"role": "assistant", "content": content})

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature
        },
        "format": "json"
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        response.raise_for_status()
        return response.json()["message"]["content"]
    except requests.exceptions.Timeout:
        logging.error(f"Timeout error when querying Ollama (timeout={timeout}s)")
        raise
    except requests.exceptions.RequestException as e:
        logging.error(f"Error querying Ollama: {e}")
        raise

def query_openai(conversation_history, api_key, model="gpt-4", temperature=0, timeout=120):
    """Query the OpenAI API with the given conversation history using requests library."""
    # OpenAI API endpoint for chat completions
    url = "https://api.openai.com/v1/chat/completions"

    # Format messages for the OpenAI API
    messages = []
    for i, content in enumerate(conversation_history):
        if i % 2 == 0:
            messages.append({"role": "user", "content": content})
        else:
            messages.append({"role": "assistant", "content": content})

    # Prepare the request payload
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": False
    }

    # if model is o3-mini, pop the temperature key
    if model == "o3-mini":
        payload.pop("temperature")

    # Define schema for regex solutions
    regex_schema = {
        "type": "object",
        "properties": {
            "explanation": {"type": "string"},
            "solutions": {
                "type": "object",
                "properties": {
                    "conservative": {
                        "type": "object",
                        "properties": {
                            "regex": {"type": "string"},
                            "explanation": {"type": "string"}
                        },
                        "required": ["regex", "explanation"],
                        "additionalProperties": False
                    },
                    "liberal": {
                        "type": "object",
                        "properties": {
                            "regex": {"type": "string"},
                            "explanation": {"type": "string"}
                        },
                        "required": ["regex", "explanation"],
                        "additionalProperties": False
                    },
                    "balanced": {
                        "type": "object",
                        "properties": {
                            "regex": {"type": "string"},
                            "explanation": {"type": "string"}
                        },
                        "required": ["regex", "explanation"],
                        "additionalProperties": False
                    }
                },
                "required": ["conservative", "liberal", "balanced"],
                "additionalProperties": False
            }
        },
        "required": ["explanation", "solutions"],
        "additionalProperties": False
    }

    # Add the response format to the payload
    payload["response_format"] = {
        "type": "json_schema",
        "json_schema": {
            "name": "regex_solutions",
            "schema": regex_schema,
            "strict": True
        }
    }

    # Set up headers with the API key
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    try:
        # Make the API request
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=timeout
        )

        # Check for HTTP errors
        response.raise_for_status()

        # Parse the response
        response_data = response.json()


        # Check if the request was refused
        if response_data["choices"][0]["message"].get("refusal", None):
            logging.error(f"OpenAI refused to generate content: {response_data['choices'][0]['message']['refusal']}")
            raise ValueError(f"OpenAI refused to generate content: {response_data['choices'][0]['message']['refusal']}")

        # Extract and return the generated content
        return response_data["choices"][0]["message"]["content"]

    except requests.exceptions.Timeout:
        logging.error(f"Timeout error when querying OpenAI (timeout={timeout}s)")
        raise
    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP error from OpenAI API: {e}")
        if response.status_code == 429:
            logging.error("Rate limit exceeded or insufficient quota")
        try:
            error_info = response.json()
            logging.error(f"OpenAI error details: {error_info}")
        except:
            pass
        raise
    except requests.exceptions.RequestException as e:
        logging.error(f"Error querying OpenAI: {e}")
        raise
    except (KeyError, IndexError) as e:
        logging.error(f"Unexpected response format from OpenAI: {e}")
        logging.debug(f"Response content: {response.text}")
        raise ValueError("Invalid response format from OpenAI API")

def parse_llm_response(response_text):
    """Parse the JSON response from the LLM."""
    try:
        response = json.loads(response_text)
        result = {
            "explanation": response.get("explanation", ""),
            "solutions": {}
        }

        # Extract the three regex patterns
        for strictness in ["conservative", "liberal", "balanced"]:
            if strictness in response.get("solutions", {}):
                solution = response["solutions"][strictness]
                result["solutions"][strictness] = {
                    "regex": solution.get("regex", ""),
                    "explanation": solution.get("explanation", "")
                }

        return result
    except json.JSONDecodeError:
        # Try to extract using regex if JSON parsing fails
        result = {"explanation": "", "solutions": {}}

        # Extract overall explanation
        explanation_match = re.search(r'"explanation":\s*"(.*?)"', response_text, re.DOTALL)
        if explanation_match:
            result["explanation"] = explanation_match.group(1)

        # Extract solution sections
        for strictness in ["conservative", "liberal", "balanced"]:
            section_match = re.search(rf'"{strictness}":\s*{{(.*?)}}', response_text, re.DOTALL)
            if section_match:
                section_content = section_match.group(1)

                # Extract regex
                regex_match = re.search(r'"regex":\s*"(.*?)"', section_content)
                # Extract explanation
                explanation_match = re.search(r'"explanation":\s*"(.*?)"', section_content, re.DOTALL)

                if regex_match:
                    result["solutions"][strictness] = {
                        "regex": regex_match.group(1),
                        "explanation": explanation_match.group(1) if explanation_match else ""
                    }

        return result
    except Exception as e:
        logging.error(f"Error parsing LLM response: {e}")
        return None

def test_regex(regex, test_strings, mode):
    """Test a regex pattern against test strings and return failures."""
    failures = []

    try:
        pattern = re.compile(regex)

        for i, test_string in enumerate(test_strings):
            string = test_string["string"]

            if mode == "full_match":
                # Full match mode
                match = exec_regex_with_timeout(pattern, string, mode)
                actual = bool(match)

                if test_string["full_match"] and not actual:
                    failures.append(f"Generated regex supposed to fully match the string {string} but it does not.\n")
                elif not test_string["full_match"] and actual:
                    failures.append(f"Generated regex should NOT fully match the string {string} but it does.\n")
                elif test_string["full_match"] and actual:
                    # No failures
                    pass
                elif not test_string["full_match"] and not actual:
                    # No failures
                    pass
            else:
                # Partial match mode
                match = exec_regex_with_timeout(pattern, string, mode)
                actual = bool(match)

                if test_string["partial_match"] and not actual:
                    failures.append(f"Generated regex supposed to partially match the substring \"{test_string['matched_string']}\" in the string \"{string}\" but it does not match any substring.\n")
                elif not test_string["partial_match"] and actual:
                    failures.append(f'Generated regex should NOT partially match ANY substring within the string "{string}" but it does match the substring "{match.group(0)}".\n')
                elif test_string["partial_match"] and actual:
                    # Check if the matched substring is correct
                    matched_string = match.group(0)
                    expected_match = test_string["matched_string"]

                    if matched_string != expected_match:
                        failures.append(f'Generated regex partially matched the substring "{matched_string}" in the string "{string}" but the matched substring is incorrect. Matched substring should be "{expected_match}".\n')
                    else:
                        # No failures
                        pass
                elif not test_string["partial_match"] and not actual:
                    # No failures
                    pass

        return failures
    except re.error as e:
        logging.error(f"Regex compilation error: {e}")
        failures.append(f"Regex failed to compile in Python: {e}")
        return failures
    except Exception as e:
        logging.error(f"Error testing regex: {e}")
        failures.append(f"There was an error testing the regex: {e}")
        return failures

def process_test_case(test_case, mode, prompts_path, api_type, url, model, temperature, max_attempts=3, timeout=120, openai_api_key=None):
    """Process a single test case and generate regex patterns."""

    # Determine the matching mode based on the test data
    if mode == "partial_match":
        initial_prompt = prepare_partial_match_prompt(test_case['strings'], prompts_path)
    elif mode == "full_match":
        initial_prompt = prepare_full_match_prompt(test_case['strings'], prompts_path)
    else:
        logging.error("Invalid mode. Please choose 'full_match' or 'partial_match'.")
        return

    # Store the final regex patterns
    final_candidates = {
        "conservative": None,
        "liberal": None,
        "balanced": None
    }

    conversation_history = [initial_prompt]
    attempts = 0
    seeked_strictness = ["conservative", "liberal", "balanced"]
    success = False
    start_time = time.time()

    # Dictionary to track trial data
    trial_data = {}
    while attempts < max_attempts:
        attempts += 1
        logging.info(f"Attempt {attempts} for test_suite_id: {test_case['test_suite_id']}")

        # Initialize trial data for this attempt
        trial_data[str(attempts)] = {
            "conservative": {"regex_pattern": None, "explanation": None, "status": "FAILED", "elapsed_time": 0},
            "liberal": {"regex_pattern": None, "explanation": None, "status": "FAILED", "elapsed_time": 0},
            "balanced": {"regex_pattern": None, "explanation": None, "status": "FAILED", "elapsed_time": 0}
        }

        try:
            # Query the LLM based on the selected API
            if api_type == "ollama":
                response_text = query_ollama(
                    conversation_history,
                    url,
                    model,
                    temperature,
                    timeout
                )
            elif api_type == "openai":
                response_text = query_openai(
                    conversation_history,
                    openai_api_key,
                    model,
                    temperature,
                    timeout,
                )
            else:
                logging.error(f"Unknown API type: {api_type}")
                return

            if not response_text:
                logging.error(f"Failed to get response from {api_type} API")
                conversation_history.append(f"Failed to get response from {api_type}. Please try again.")

            # Parse the response
            parsed_response = parse_llm_response(response_text)
            if not parsed_response:
                logging.error("Failed to parse LLM response")
                conversation_history.append("Your response format was incorrect. Please provide your response in provided JSON format.")
                continue

            conversation_history.append(response_text)

            # Test each regex pattern
            all_patterns_valid = True
            feedback = {}

            for strictness in seeked_strictness[:]:
                if strictness not in parsed_response.get("solutions", {}):
                    all_patterns_valid = False
                    feedback[strictness] = "Missing regex pattern"
                    continue

                regex = parsed_response["solutions"][strictness]["regex"]
                explanation = parsed_response["solutions"][strictness].get("explanation", "")

                # Store trial data
                trial_data[str(attempts)][strictness]["regex_pattern"] = regex
                trial_data[str(attempts)][strictness]["explanation"] = explanation

                failures = test_regex(regex, test_case['strings'], mode)

                if not failures:
                    final_candidates[strictness] = regex
                    trial_data[str(attempts)][strictness]["status"] = "SUCCESS"
                    trial_data[str(attempts)][strictness]["elapsed_time"] = (time.time() - start_time) * 1000 # Convert to milliseconds
                    if strictness in seeked_strictness:
                        seeked_strictness.remove(strictness)
                else:
                    all_patterns_valid = False
                    trial_data[str(attempts)][strictness]["status"] = "FAILED"
                    trial_data[str(attempts)][strictness]["elapsed_time"] = (time.time() - start_time) * 1000 # Convert to milliseconds
                    feedback[strictness] = failures

            # If all patterns are valid, we're done
            if all(final_candidates.values()):
                success = True
                break

            # Otherwise, generate feedback for the next attempt
            strictness_mention_in_feedback_prompt = ", ".join([strictness for strictness in feedback.keys() if feedback[strictness]])
            feedback_prompt = f"I need you to revise your {strictness_mention_in_feedback_prompt} regex patterns. Keep the output format same. {'' if not strictness_mention_in_feedback_prompt else 'You do not need to change not mentioned regex patterns. '}Here is the feedback:\n\n"

            for strictness, strictness_feedback in feedback.items():
                if strictness not in seeked_strictness:
                    continue

                if not final_candidates[strictness] and strictness_feedback:
                    formatted_feedback = "".join(strictness_feedback)
                    feedback_prompt += f"For {strictness} regex:\n{formatted_feedback}\n\n"

            conversation_history.append(feedback_prompt)

        except requests.exceptions.Timeout as e:
            logging.error(f"Timeout in attempt {attempts} for test_suite_id {test_case['test_suite_id']}: Request timed out after {timeout} seconds")

            # Mark all regex types as EXCEPTION in trial data
            for strictness in ["conservative", "liberal", "balanced"]:
                trial_data[str(attempts)][strictness]["status"] = "EXCEPTION"
                trial_data[str(attempts)][strictness]["explanation"] = f"Timeout after {timeout} seconds"
                trial_data[str(attempts)][strictness]["elapsed_time"] = (time.time() - start_time) * 1000 # Convert to milliseconds

            # Treat timeout as a failed attempt and continue if there are attempts remaining
            if attempts < max_attempts:
                error_feedback = f"Request timed out after {timeout} seconds. Let's try again."
                conversation_history.append(error_feedback)

        except Exception as e:
            logging.error(f"Error in attempt {attempts} for test_suite_id {test_case['test_suite_id']}: {e}")

            # Mark all regex types as EXCEPTION in trial data
            for strictness in ["conservative", "liberal", "balanced"]:
                trial_data[str(attempts)][strictness]["status"] = "EXCEPTION"
                trial_data[str(attempts)][strictness]["explanation"] = str(e)
                trial_data[str(attempts)][strictness]["elapsed_time"] = (time.time() - start_time) * 1000 # Convert to milliseconds

            if attempts < max_attempts:
                error_feedback = f"An error occurred: {str(e)}. Let's try again."
                conversation_history.append(error_feedback)

    # Calculate elapsed time
    elapsed_time = (time.time() - start_time) * 1000 # Convert to milliseconds

    # Determine the status based on successful regex patterns
    status = "FAILED"

    # Check which regex types were successful
    successful_types = []
    if final_candidates["conservative"]:
        successful_types.append("C")
    if final_candidates["balanced"]:
        successful_types.append("B")
    if final_candidates["liberal"]:
        successful_types.append("L")

    if len(successful_types) == 3:
        status = "SUCCESS"
    elif len(successful_types) > 0:
        # Sort to ensure consistent ordering (C, B, L)
        successful_types.sort()
        status = "PARTIAL_SUCCESS_" + "".join(successful_types)

    # for hist in conversation_history:
    #     print(hist)

    # Prepare the output
    output = {
        "regex_id": test_case["regex_id"],
        "project_id": test_case["project_id"],
        "test_suite_id": test_case["test_suite_id"],
        "regex_pattern": test_case["regex_pattern"],
        "strings": test_case["strings"],
        "candidates": [
            {"type": "conservative", "regex": final_candidates["conservative"]},
            {"type": "liberal", "regex": final_candidates["liberal"]},
            {"type": "balanced", "regex": final_candidates["balanced"]}
        ],
        "test_string_count": test_case["test_string_count"],
        "elapsed_time": elapsed_time,
        "status": status,
        "trials": trial_data
    }

    return output

def process_file(input_file, output_file, mode, prompts_path, api_type, url, model, temperature=0, max_attempts=3, timeout=120, output_trials=False, openai_api_key=None):
    """Process all test cases in the input file and write results to the output file."""
    # Create output directory if it doesn't exist
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Create trials output file if enabled
    trials_out_f = None
    if output_trials:
        trials_output_file = f"{output_file}_trials"
        trials_out_f = open(trials_output_file, 'w')
        logging.info(f"Writing trial data to {trials_output_file}")

    with open(output_file, 'w') as out_f:
        # for test_case in read_input_file(input_file):
        for test_case in tqdm(read_input_file(input_file)):
            logging.info(f"Processing test_suite_id: {test_case['test_suite_id']}")

            # Process the test case - exceptions are now handled inside process_test_case
            result = process_test_case(test_case, mode, prompts_path, api_type, url, model, temperature, max_attempts, timeout, openai_api_key)

            # Extract trial data
            trial_data = result.pop("trials", {})

            # Write result to output file
            out_f.write(json.dumps(result) + '\n')
            out_f.flush()  # Ensure the data is written to disk

            # Write trial data if enabled
            if output_trials and trials_out_f:
                trials_out_f.write(json.dumps(trial_data) + '\n')
                trials_out_f.flush()

    # Close trials output file if opened
    if trials_out_f:
        trials_out_f.close()

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Generate regex patterns using LLM.")
    parser.add_argument("--input", "-i", required=True, help="Input NDJSON file path")
    parser.add_argument("--output", "-o", required=True, help="Output NDJSON file path")
    parser.add_argument("--url", "-u", default="http://localhost:11434/api/chat", help="Ollama API URL")
    parser.add_argument("--model", "-m", required=True, default="mistral:latest", help="Ollama model to use")
    parser.add_argument("--attempts", "-a", type=int, default=3, help="Maximum number of attempts")
    parser.add_argument("--temperature", "-t", type=float, default=0, help="Temperature for LLM")
    parser.add_argument("--prompts-path", "-p", default="prompts", help="Path to the prompts directory")
    parser.add_argument("--output-trials", action="store_true", help="Output trial data to a separate file")
    parser.add_argument("--mode", "-md", default="full_match", choices=["full_match", "partial_match"], help="Matching mode")
    parser.add_argument("--timeout", "-to", type=int, default=120, help="Timeout for LLM requests")
    parser.add_argument("--openai-api-key", "-k", default=None, help="OpenAI API key")
    parser.add_argument("--api-type", "-api", default="ollama", choices=["ollama", "openai"], help="API type")
    parser.add_argument("--log-level", "-l", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Set the logging level")

    args = parser.parse_args()

    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    logging.info(f"Starting regex generation with model: {args.model}")
    process_file(args.input, args.output, args.mode, args.prompts_path, args.api_type, args.url, args.model, args.temperature, args.attempts, args.timeout, args.output_trials, args.openai_api_key)
    logging.info("Regex generation completed")

if __name__ == "__main__":
    main()