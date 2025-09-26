#!/usr/bin/env python3
"""
Ray-parallelized Strictness Score Calculator for Regex Candidates

This script calculates strictness scores for regex candidates
in both rbe_generated_candidates and llm_generated_candidates tables using Ray
for distributed processing.
"""

import os
import subprocess
import sys
import argparse
import datetime
import tempfile
import time
import logging
import traceback
from typing import List, Dict, Optional, Tuple, Union
from dataclasses import dataclass
from contextlib import contextmanager
import uuid
import orjson
from peewee import JOIN
import ray
from tqdm import tqdm
import regex_generation
from metrics.ray_status_tracker import RayStatusTracker
import re
import regex as rx
rx.DEFAULT_VERSION = rx.VERSION1

from regex_generation.synthesizers.RegexPlus.synthesis import entrypoint as regexplus_entrypoint

from playhouse.sqlite_ext import SqliteExtDatabase
from regex_generation.db.models import (
    RbeGeneratedCandidate, LlmGeneratedCandidate, StrictnessScore,
    RbeGenerationQuery, LlmGenerationQuery, SynthesizerGeneratedCandidate, SynthesizerGenerationQuery, SynthesizerGenerationTask, db_proxy
)
import metrics
from metrics.strictness_score.strictness_score import calculate_strictness_score
from metrics.strictness_score.strictness_score2 import strictness_score_from_regex_and_positives

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

os.environ["RAY_IGNORE_UNHANDLED_ERRORS"] = "1"

def run_rfixer(positive_strings, negative_strings, path_to_synthesizer):
    # Run RFixer on the dataset
    """
    RFixer needs an input file with the following format:
    .
    +++
    Positive examples, one per line
    ---
    Negative examples, one per line
    """

    rfixer_sol_regex = re.compile(r'\#sol\#(.*)\#sol\#')

    EMPTY_GROUND_TRUTH = '.'
    error_message = None

    # Create a temporary file for the actual run
    with tempfile.NamedTemporaryFile(mode='w', delete=True) as temp_file:
        temp_file.write(EMPTY_GROUND_TRUTH + '\n')
        temp_file.write('+++\n')
        for example in positive_strings:
            temp_file.write(example + '\n')
        temp_file.write('---\n')
        for example in negative_strings:
            temp_file.write(example + '\n')

        # Make sure the data is written to the file
        temp_file.flush()

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
                cwd=cwd
            ).decode('utf-8')
            status = "success"
        except subprocess.CalledProcessError as e:
            error_message = str(e)
            status = "error"

    # Parse the output
    if status != "error":
        # Parse this part of the output: "solution is #sol#<regex>#sol#"
        parsed_regex = rfixer_sol_regex.search(cmd_output)
        sol_found = bool(parsed_regex)

        if sol_found:
            parsed_regex = parsed_regex.group(1)
            status = "success"
        else:
            parsed_regex = 'Solution not found!'
            status = "solution_not_found"

    if status != "error" and status != "solution_not_found":
        candidate_regex = parsed_regex

    output_dict = {
        'candidates': [candidate_regex] if (status != "error" and status != "solution_not_found") else [],
        'status': status,
        'error_message': error_message
    }

    return output_dict

def run_forest(positive_strings, negative_strings, path_to_synthesizer):
    """
    FOREST needs an input file with the following format:
    ++
    Positive examples, one per line
    --
    Negative examples, one per line
    """

    error_message = None

    # Create a temporary file for the actual run
    with tempfile.NamedTemporaryFile(mode='w', delete=True) as temp_file:
        temp_file.write('++\n')
        for example in positive_strings:
            temp_file.write(example + '\n')
        temp_file.write('--\n')
        for example in negative_strings:
            temp_file.write(example + '\n')

        # Make sure the data is written to the file
        temp_file.flush()

        # Run FOREST using the temporary file
        command = f'python3 {path_to_synthesizer.split("/")[-1]} --no-disambiguation {temp_file.name}'
        try:
            # From command remove the file name and CD to the directory
            cmd_output = subprocess.check_output(
                command,
                shell=True,
                cwd="/".join(path_to_synthesizer.split('/')[:-1]),
            ).decode('utf-8')
            status = "success"
        except subprocess.CalledProcessError as e:
            status = "error"
            error_message = str(e)

    # Parse the output
    if status != "error":
        if 'Solution not found!' in cmd_output:
            parsed_regex = 'Solution not found!'
            status = "solution_not_found"
        else:
            parsed_regex = cmd_output.split('Solution:\n')[1].split('\n')[0][2:]
            status = "success"

    if status != "error" and status != "solution_not_found":
        candidate_regex = parsed_regex

    output_dict = {
        'candidates': [candidate_regex] if (status != "error" and status != "solution_not_found") else [],
        'status': status,
        'error_message': error_message
    }

    return output_dict

def run_regexplus(positive_strings, negative_strings, path_to_synthesizer):
    """
    RegexPlus needs an input file with the following format:
    ++
    Positive examples, one per line
    --
    Negative examples, one per line
    """
    error_message = None
    candidate_list = []

    try:
        output = regexplus_entrypoint(positive_strings)
        status = "success"
        for candidate in output:
            candidate_list.append(candidate)
    except Exception as e:
        status = "error"
        error_message = str(e)

    if len(candidate_list) == 0:
        status = "solution_not_found"

    output_dict = {
        'candidates': candidate_list if (status != "error" and status != "solution_not_found") else [],
        'status': status,
        'error_message': error_message
    }
    print(output_dict)
    return output_dict

@dataclass
class RegexCompositionTask:
    task_id: str
    ground_truth: str
    positive_strings: List[str]
    negative_strings: List[str]

@dataclass
class CandidateData:
    """Data structure for candidate regex information"""
    candidate_id: str
    candidate_type: str  # 'rbe' or 'llm'
    regex_pattern: str
    positive_examples: List[str]
    negative_examples: List[str]


@dataclass
class SynthesizerResult:
    candidates: List[str]
    status: str
    error_message: Optional[str] = None


@ray.remote
def process_single_task(
    task: RegexCompositionTask,
    job_id: str,
    status_tracker: RayStatusTracker,
    synthesizer: str,
    path_to_synthesizer: str,
    timeout: Optional[float] = None
) -> SynthesizerResult:
    """Ray task for processing a single candidate (database updates handled centrally)"""

    try:
        # mark that this task actually began (so queued-but-not-started tasks won't timeout)
        try:
            status_tracker.mark_started.remote(job_id)
        except Exception as e:
            pass # don't let bookkeeping affect work

        if synthesizer == 'RFixer':
            output = run_rfixer(task.positive_strings, task.negative_strings, path_to_synthesizer)
        elif synthesizer == 'FOREST':
            output = run_forest(task.positive_strings, task.negative_strings, path_to_synthesizer)
        elif synthesizer == 'RegexPlus':
            output = run_regexplus(task.positive_strings, task.negative_strings, path_to_synthesizer)
        else:
            raise ValueError(f"Unsupported synthesizer: {synthesizer}")

        result = SynthesizerResult(
            candidates=list(output.get("candidates", [])),
            status=output.get("status", "error"),
            error_message=output.get("error_message")
        )

    except Exception as e:
        logger.error(f"Error processing task {task.task_id}: {e}")
        result = SynthesizerResult(
            candidates=[],
            error_message=str(e),
            status="error"
        )
    return result


class SynthesizerRunner:
    """Main class for running synthesizers using Ray with centralized database updates"""

    def __init__(
        self,
        db_path: str,
        input_file: str,
        synthesizer: str,
        path_to_synthesizer: str,
        experiment_id: str,
        num_workers: Optional[int] = None,
        use_actors: bool = True,
        timeout: Optional[float] = None,
    ):
        # Ensure database path is absolute and exists
        self.db_path = os.path.abspath(db_path)

        self.input_file = input_file
        self.synthesizer = synthesizer
        self.path_to_synthesizer = path_to_synthesizer
        self.experiment_id = experiment_id
        self.use_actors = use_actors
        self.timeout = timeout

        # Initialize Ray if not already initialized
        if not ray.is_initialized():
            ray.init(runtime_env={"py_modules": [metrics, regex_generation.synthesizers, regex_generation.db.models]})

        # Get available resources
        resources = ray.available_resources()
        available_cpus = int(resources.get("CPU", 1))
        self.num_workers = num_workers or available_cpus

        logger.info(f"Initialized with {self.num_workers} workers for centralized database updates")

    def create_schema_if_needed(self):
        """Create schema if needed"""
        with self._get_connection() as db:
            db.create_tables([SynthesizerGenerationTask, SynthesizerGenerationQuery, SynthesizerGeneratedCandidate])

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        db = SqliteExtDatabase(
            self.db_path,
            pragmas={
                'foreign_keys': 1,
                'journal_mode': 'wal',
                'cache_size': -64_000
            }
        )
        db_proxy.initialize(db)
        try:
            yield db
        finally:
            db.close()

    def _load_tasks(self):
        """Load NDJSON file into tasks"""
        tasks = []
        with open(self.input_file, "rb") as f:
            for line in f:
                data = orjson.loads(line)

                task = RegexCompositionTask(
                    task_id=data.get("test_suite_id"),
                    ground_truth=data.get("regex"),
                    positive_strings=[s.get("subject") for s in data.get("positive_strings", [])],
                    negative_strings=[s.get("subject") for s in data.get("negative_strings", [])]
                )

                tasks.append(task)
        return tasks

    def _calculate_regex_accuracy(self, regex_pattern: str, positive_strings: List[str], negative_strings: List[str]) -> float:
        """Calculate the accuracy of a regex pattern"""
        total = len(positive_strings) + len(negative_strings)
        correct = 0

        try:
            rx.compile(regex_pattern)
        except Exception as e:
            return 0.0

        for s in positive_strings:
            try:
                if rx.fullmatch(regex_pattern, s, timeout=3):
                    correct += 1
            except Exception as e:
                pass
        for s in negative_strings:
            try:
                if not rx.fullmatch(regex_pattern, s, timeout=3):
                    correct += 1
            except Exception as e:
                pass

        accuracy = correct / max(1, total)

        return accuracy

    def _update_result_in_database(self, query: SynthesizerGenerationQuery, result: SynthesizerResult, status: str, generation_time: float, use_result_status: bool = True):
        """Update database with result (centralized database updates)"""
        try:
            with self._get_connection() as db:
                with db.atomic():
                    candidates = result.candidates

                    # Load positive/negative examples from the task linked to this query
                    positive_examples = query.task.positive_examples if query and query.task else []
                    negative_examples = query.task.negative_examples if query and query.task else []

                    for candidate_regex in candidates:
                        accuracy = self._calculate_regex_accuracy(candidate_regex, positive_examples, negative_examples)

                        SynthesizerGeneratedCandidate.create(
                            query=query,
                            regex_pattern=candidate_regex,
                            accuracy=accuracy,
                            generation_time=generation_time
                        )
                # Update query status
                if use_result_status:
                    query.status = result.status
                else:
                    query.status = status
                # Persist any error message coming from the synthesizer
                query.error_message = result.error_message
                query.save()

        except Exception as e:
            logger.error(f"Error updating database for query {getattr(query, 'id', None)}: {e}")

        # All database updates are now handled centrally in the main collection loop

    def generate_candidates(
        self,
        show_progress: bool = True,
    ) -> Dict[str, int]:
        """
        Calculate strictness scores for all candidates with improved timeout handling

        Args:
            show_progress: Show progress bars

        Returns:
            Dictionary with processing statistics
        """
        start_time = time.time()

        logger.info(f"Loading candidates from NDJSON for {self.synthesizer}")
        all_tasks = self._load_tasks()
        logger.info(f"Loaded {len(all_tasks)} tasks")

        if not all_tasks:
            logger.info("No tasks need processing")
            return {"processed": 0, "updated": 0, "errors": 0, "timeouts": 0}

        logger.info(f"Processing {len(all_tasks)} tasks with {self.num_workers} workers")

        # Helper function to create error result
        def create_error_result(status, error_message):
            return SynthesizerResult(
                candidates=[],
                status=status,
                error_message=error_message
            )

        # Submit all candidates for processing
        futures_map = {}  # Maps future -> (task, query, submit_time, job_id)
        status_tracker = RayStatusTracker.remote()
        mem_bytes = 1024 * 1024 * 1024 * 4 # 4GB
        query: SynthesizerGenerationQuery = None

        with tqdm(total=len(all_tasks), desc=f"Submitting {self.synthesizer} tasks", disable=not show_progress) as pbar:
            for i, task in enumerate(all_tasks):
                # First check if the task already exists in the database
                with self._get_connection() as db:
                    with db.atomic():
                        existing_task = SynthesizerGenerationTask.select().where(SynthesizerGenerationTask.ground_truth == task.ground_truth, SynthesizerGenerationTask.positive_examples == task.positive_strings, SynthesizerGenerationTask.negative_examples == task.negative_strings).first()

                        if not existing_task:
                            existing_task = SynthesizerGenerationTask.create(
                                ground_truth=task.ground_truth,
                                positive_examples=task.positive_strings,
                                negative_examples=task.negative_strings
                            )

                        query_parameters = {
                            "synthesizer": self.synthesizer,
                            "experiment_id": self.experiment_id,
                            "timeout": self.timeout
                        }

                        # Get the queries for this task
                        queries = SynthesizerGenerationQuery.select().where((SynthesizerGenerationQuery.task == existing_task) & (SynthesizerGenerationQuery.query_parameters == query_parameters))

                        # If we have queries, we don't need to process the task again
                        if queries.exists():
                            logger.info(f"Skipping task {task.task_id} because it already has queries")
                            continue
                        else:
                            # Create the query
                            query = SynthesizerGenerationQuery.create(
                                task=existing_task,
                                query_parameters=query_parameters,
                                status="pending"
                            )

                job_id = f"{getattr(task,'task_id', i)}-{uuid.uuid4().hex}"
                future = process_single_task.options(
                    memory=mem_bytes
                ).remote(
                    task,
                    job_id,
                    status_tracker,
                    synthesizer=self.synthesizer,
                    path_to_synthesizer=self.path_to_synthesizer,
                    timeout=self.timeout
                )

                futures_map[future] = (task, query, time.time(), job_id)
                pbar.update(1)

        # Process results with improved timeout handling
        all_results = []
        pending = list(futures_map.keys())

        with tqdm(total=len(pending), desc="Processing & updating", disable=not show_progress) as pbar:
            while pending:
                # Calculate timeout for ray.wait
                wait_timeout = 1.0  # Default poll interval

                if self.timeout:
                    # Find the oldest pending task
                    oldest_submit_time = min(futures_map[ref][2] for ref in pending)
                    elapsed = time.time() - oldest_submit_time
                    remaining = max(0, self.timeout - elapsed)
                    wait_timeout = min(1.0, remaining)  # Check at least every second

                # Wait for results with timeout
                ready, still_pending = ray.wait(
                    pending,
                    num_returns=len(pending),  # Get all ready results at once
                    timeout=wait_timeout
                )

                # Process all ready results
                for ref in ready:
                    task, task_query, submit_time, job_id = futures_map.pop(ref, (None, None, None, None))
                    if task is None:
                        continue # task was already cancelled
                    task_id = getattr(task, "task_id", "unknown")

                    try:
                        # Get result (should be immediate since it's ready)
                        result = ray.get(ref, timeout=0.1)
                        all_results.append(result)
                        self._update_result_in_database(task_query, result, "success", round(time.time() - submit_time, 3), use_result_status=True)
                        logger.debug(f"✓ Task ID {task_id} processed successfully")

                    except (ray.exceptions.RayTaskError, ray.exceptions.RayActorError, ray.exceptions.OutOfMemoryError, Exception) as e:
                        # Handle any errors uniformly
                        error_result = create_error_result(
                            "error",
                            str(e)
                        )
                        all_results.append(error_result)
                        if task_id != "unknown":
                            self._update_result_in_database(task_query, error_result, "error", round(time.time() - submit_time, 3), use_result_status=False)
                        logger.debug(f"✗ Task ID {task_id} failed: {str(e)}")

                    pbar.update(1)

                # Handle timeouts if enabled
                if self.timeout and still_pending:
                    job_ids = [futures_map[ref][3] for ref in still_pending]
                    started_times = ray.get(status_tracker.get_started_times.remote(job_ids))
                    current_time = time.time()
                    newly_timed_out = []

                    for ref in still_pending:
                        task, task_query, submit_time, job_id = futures_map[ref]
                        started_at = started_times.get(job_id)

                        if started_at is None:
                            continue # not yet running -> don't timeout

                        if current_time - started_at >= self.timeout:
                            # This task has timed out
                            newly_timed_out.append(ref)

                            # Cancel the task
                            try:
                                ray.cancel(ref, force=True, recursive=True)
                            except Exception:
                                pass  # Cancellation might fail if task just completed

                            # Create timeout result
                            task_id = getattr(task, "task_id", "unknown")
                            timeout_result = create_error_result(
                                "timeout",
                                "Synthesizer timed out"
                            )
                            all_results.append(timeout_result)
                            if task_id != "unknown":
                                self._update_result_in_database(task_query, timeout_result, "timeout", round(time.time() - submit_time, 3), use_result_status=False)
                            logger.debug(f"⏱ Task ID {task_id} timed out")

                            # Remove from futures_map
                            futures_map.pop(ref, None)
                            pbar.update(1)

                    # Update pending list
                    pending = [ref for ref in still_pending if ref not in newly_timed_out]
                else:
                    pending = still_pending

                # Update progress bar description with real-time stats
                stats_counts = {
                    "success": sum(1 for r in all_results if r.status == "success"),
                    "error": sum(1 for r in all_results if r.status == "error"),
                    "timeout": sum(1 for r in all_results if r.status == "timeout")
                }
                pbar.set_description(
                    f"Processing & updating (✓{stats_counts['success']} "
                    f"✗{stats_counts['error']} ⏱{stats_counts['timeout']})"
                )

        logger.info("All tasks processed and database updated")

        # Calculate final statistics
        stats = {
            "processed": len(all_results),
            "updated": sum(1 for r in all_results if r.status == "success"),
            "errors": sum(1 for r in all_results if r.status == "error"),
            "timeouts": sum(1 for r in all_results if r.status == "timeout")
        }

        elapsed = time.time() - start_time
        logger.info(f"Processing complete in {elapsed:.2f} seconds")
        logger.info(f"Statistics: {stats}")

        return stats

    def shutdown(self):
        """Clean up Ray resources"""
        if self.use_actors and hasattr(self, 'workers'):
            for worker in self.workers:
                try:
                    worker.shutdown.remote()
                except Exception:
                    pass
        logger.info("Ray resources cleaned up")


def build_args() -> argparse.Namespace:
    """Build command line arguments"""
    p = argparse.ArgumentParser(
        description="Query synthesizers for regex generation."
    )

    p.add_argument("--input-file", required=True, help="Path to input NDJSON with positive and negative strings")
    p.add_argument("--sqlite-db", required=True, help="Path to SQLite database to store results")
    p.add_argument('--synthesizer', type=str, help='Name of the synthesizer to run', required=True, choices=['FOREST', 'RFixer', 'RegexPlus'])
    p.add_argument('--path-to-synthesizer', type=str, help='Path to the synthesizer executable', required=True)
    p.add_argument("--experiment-id", type=str, default=None, help="Experiment ID for tracking queries")
    p.add_argument(
        "--num-workers", type=int, default=None,
        help="Number of Ray workers (default: all available CPUs in the cluster)"
    )
    p.add_argument(
        "--timeout", type=float, default=30.0,
        help="Timeout for synthesizer execution (seconds)"
    )
    p.add_argument(
        "--no-progress", action="store_true",
        help="Disable progress bars"
    )
    return p.parse_args()


def main():
    """Main function"""
    args = build_args()

    try:
        # Initialize calculator
        synthesizer_runner = SynthesizerRunner(
            db_path=args.sqlite_db,
            input_file=args.input_file,
            synthesizer=args.synthesizer,
            path_to_synthesizer=args.path_to_synthesizer,
            experiment_id=args.experiment_id,
            num_workers=args.num_workers,
            timeout=args.timeout,
        )

        # Create database schema if needed
        synthesizer_runner.create_schema_if_needed()

        # Calculate scores
        stats = synthesizer_runner.generate_candidates(
            show_progress=not args.no_progress,
        )

        # Print final statistics
        print(f"\nFinal Results:")
        print(f"  Processed: {stats['processed']}")
        print(f"  Successfully updated: {stats['updated']}")
        print(f"  Errors: {stats['errors']}")
        print(f"  Timeouts: {stats['timeouts']}")

        # Clean up
        synthesizer_runner.shutdown()

        return 0

    except Exception as e:
        print(traceback.format_exc())
        logger.error(f"Fatal error: {e}")
        return 1
    finally:
        # Ensure Ray is shut down
        if ray.is_initialized():
            ray.shutdown()


if __name__ == "__main__":
    sys.exit(main())