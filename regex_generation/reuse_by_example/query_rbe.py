#!/usr/bin/env python3
"""
High-Performance Regex Matcher with Python multiprocessing (mrab-regex) — single file

- Scans a SQLite table of regexes: columns (id INTEGER PRIMARY KEY, pattern TEXT)
- Matches against per-query positive/negative example sets
- Thresholds on positive and negative accuracy
- Parallelized with Python multiprocessing (no Ray)
- Persists results via Peewee models you provide in db.models

Dependencies:
  pip install regex peewee orjson tqdm playhouse
"""

import argparse
import datetime
import logging
import math
import os
import signal
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import List, Optional, Tuple

import orjson
import regex as rx
from multiprocessing import Pool, get_context, cpu_count
from playhouse.sqlite_ext import SqliteExtDatabase
from tqdm import tqdm

# Your package with Peewee models
from regex_generation.db.models import (  # noqa: E402
    RbeGeneratedCandidate,
    RbeGenerationQuery,
    RbeGenerationTask,
    db_proxy,
)

SLOW_REGEX_IDS = [
    86147,
    2693143,
    1522013,
    1522014,
    1522016,
    1522017,
]

# Ensure consistent regex behavior
rx.DEFAULT_VERSION = rx.VERSION1

# --------------------------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("mp_regex_matcher")

# Helpful to avoid thread oversubscription if any deps use BLAS/OpenMP
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

# --------------------------------------------------------------------------------------
# Domain dataclasses
# --------------------------------------------------------------------------------------
@dataclass
class MatchResult:
    """Result of regex matching against string sets."""
    regex_id: int
    pattern: str
    positive_matches: int
    negative_matches: int
    positive_accuracy: float
    negative_accuracy: float
    meets_threshold: bool


@dataclass
class Partition:
    """Defines a data partition by its start and end ID."""
    start_id: int
    end_id: int
    partition_index: int


# --------------------------------------------------------------------------------------
# SQLite helpers
# --------------------------------------------------------------------------------------
def _get_db_connection(db_path: str, read_only: bool = True):
    """Standalone function to get a SQLite connection."""
    uri_path = db_path.replace("\\", "/")
    if read_only:
        uri = f"file:{uri_path}?mode=ro&immutable=1"
        conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
    else:
        conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Pragmas tuned for fast read-mostly workloads
    conn.execute("PRAGMA synchronous = OFF;")
    conn.execute("PRAGMA temp_store = MEMORY;")
    conn.execute("PRAGMA mmap_size = 268435456;")
    conn.execute("PRAGMA cache_size = -64000;")
    return conn


def _build_partition_query(include_source: str) -> str:
    """Builds a single SELECT for all regexes in a partition, filtered by source."""
    base_query = (
        "SELECT DISTINCT r.id, r.pattern "
        "FROM regex_entity r "
        "JOIN regex_source_usage rsu ON r.id = rsu.regex_id "
    )
    clause_map = {
        "internet": "JOIN project_spec p ON p.id = rsu.project_id "
                    "WHERE p.name IN ('RegExLib', 'Stack Overflow Posts', 'Stack Overflow Comments') "
                    "AND r.id >= ? AND r.id <= ?",
        "oss": "JOIN project_spec p ON p.id = rsu.project_id "
               "WHERE p.name NOT IN ('RegExLib', 'Stack Overflow Posts', 'Stack Overflow Comments') "
               "AND r.id >= ? AND r.id <= ?",
        "all": "WHERE r.id >= ? AND r.id <= ?",
    }
    return f"{base_query}{clause_map[include_source]} ORDER BY r.id"


# --------------------------------------------------------------------------------------
# Core matching routine (same logic)
# --------------------------------------------------------------------------------------
def _is_timeout_exc(e):
    # Be tolerant to different names across regex versions/platforms
    name = e.__class__.__name__
    return (
        name in ("TimeoutError", "RegexTimeoutError") or
        getattr(rx, "TimeoutError", None) and isinstance(e, rx.TimeoutError)
    )

def _match_regexes_core(
    regex_items,
    positive_strings,
    negative_strings,
    targeted_pos_accuracy,
    targeted_neg_accuracy,
    timeout,
    *,
    max_timeouts_per_regex=3,
    max_wall_per_regex=1.0,
):
    results: List[MatchResult] = []
    pos_count = len(positive_strings)
    neg_count = len(negative_strings)

    min_pos_matches = int(math.ceil(pos_count * targeted_pos_accuracy)) if pos_count else 0
    max_neg_matches = int(math.floor(neg_count * (1.0 - targeted_neg_accuracy))) if neg_count else 0

    for regex_id, pattern in regex_items:
        start = time.perf_counter()
        timeouts = 0

        try:
            compiled = rx.compile(pattern)
        except Exception:
            continue

        # POSITIVES
        pos_matches = 0
        skip = False
        for s in positive_strings:
            # fuse check
            if (time.perf_counter() - start) > max_wall_per_regex or timeouts > max_timeouts_per_regex:
                logger.warning(f"Skipping slow regex {regex_id}: wall={time.perf_counter()-start:.3f}s timeouts={timeouts}")
                skip = True
                break
            try:
                if compiled.fullmatch(s, timeout=timeout):
                    pos_matches += 1
            except Exception as e:
                if _is_timeout_exc(e):
                    timeouts += 1
                # ignore other match errors for this string and continue
                continue

        if skip or pos_matches < min_pos_matches:
            continue

        # NEGATIVES (early abort as soon as we exceed allowed false positives)
        neg_matches = 0
        for s in negative_strings:
            if (time.perf_counter() - start) > max_wall_per_regex or timeouts > max_timeouts_per_regex:
                logger.warning(f"Skipping slow regex {regex_id}: wall={time.perf_counter()-start:.3f}s timeouts={timeouts} pat={pattern!r}")
                skip = True
                break
            try:
                if compiled.fullmatch(s, timeout=timeout):
                    neg_matches += 1
                    if neg_matches > max_neg_matches:
                        break
            except Exception as e:
                if _is_timeout_exc(e):
                    timeouts += 1
                continue

        if skip or neg_matches > max_neg_matches:
            continue

        pos_accuracy = (pos_matches / pos_count) if pos_count else 1.0
        neg_accuracy = 1.0 - ((neg_matches / neg_count) if neg_count else 0.0)

        if pos_accuracy >= targeted_pos_accuracy and neg_accuracy >= targeted_neg_accuracy:
            results.append(MatchResult(
                regex_id=regex_id, pattern=pattern,
                positive_matches=pos_matches, negative_matches=neg_matches,
                positive_accuracy=pos_accuracy, negative_accuracy=neg_accuracy,
                meets_threshold=True
            ))
    return results


# --------------------------------------------------------------------------------------
# Multiprocessing worker plumbing
# --------------------------------------------------------------------------------------
# Set at process start by _init_worker; used read-only in workers.
_G_POS: List[str] = []
_G_NEG: List[str] = []


def _init_worker(positive_strings, negative_strings):
    """Initializer run once per worker process to cache example sets in-process."""
    global _G_POS, _G_NEG
    signal.signal(signal.SIGINT, signal.SIG_IGN)  # let main handle Ctrl+C
    # Normalize to lists of str
    _G_POS = list({str(s) for s in positive_strings if s is not None})
    _G_NEG = list({str(s) for s in negative_strings if s is not None})
    # Ensure regex module version inside workers
    rx.DEFAULT_VERSION = rx.VERSION1
    logger.info(f"[worker {os.getpid()}] cached {len(_G_POS)} pos / {len(_G_NEG)} neg")


def _worker_process_regexes(args):
    """Process one chunk of (id, pattern) pairs using globals set by _init_worker."""
    (regex_items, targeted_pos_accuracy, targeted_neg_accuracy, timeout, max_timeouts_per_regex, max_wall_per_regex) = args
    return _match_regexes_core(
        regex_items,
        _G_POS,
        _G_NEG,
        targeted_pos_accuracy,
        targeted_neg_accuracy,
        timeout,
        max_timeouts_per_regex=max_timeouts_per_regex,
        max_wall_per_regex=max_wall_per_regex,
    )


def _split_into_n_slices(total_len: int, n_slices: int):
    if n_slices <= 0 or total_len <= 0:
        return []
    # ceil so we cover everything
    chunk = math.ceil(total_len / n_slices)
    return [(i*chunk, min((i+1)*chunk, total_len)) for i in range(n_slices) if i*chunk < total_len]


# --------------------------------------------------------------------------------------
# Matcher (MP implementation)
# --------------------------------------------------------------------------------------
class MPRegexMatcher:
    def __init__(
        self,
        db_path: str,
        sqlite_db: str,
        num_partitions: int,
        workers_per_partition: int,
        read_only: bool = True,
        include_source: str = "all",
        experiment_id: Optional[str] = None,
        start_method: Optional[str] = None,  # e.g., "fork" (Linux default) or "spawn"
        maxtasks_per_child: int = 0,         # 0 = unlimited; set >0 to mitigate leaks
    ):
        self.db_path = os.path.abspath(db_path)
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database file not found: {self.db_path}")

        self.sqlite_db = sqlite_db
        self.num_partitions = max(1, num_partitions)
        self.workers_per_partition = max(1, workers_per_partition)
        self.total_workers = self.num_partitions * self.workers_per_partition
        self.read_only = read_only
        self.include_source = include_source
        self.experiment_id = experiment_id
        self.start_method = start_method
        self.maxtasks_per_child = maxtasks_per_child

        with _get_db_connection(self.db_path) as conn:
            self.total_regexes, self.min_id, self.max_id = self._get_db_stats(conn)

        logger.info(
            f"Initializing MP matcher with {self.num_partitions} partitions x "
            f"{self.workers_per_partition} workers = {self.total_workers} total processes."
        )
        logger.info(f"Total regexes in database: {self.total_regexes:,} (IDs {self.min_id}-{self.max_id})")

    @contextmanager
    def _get_result_db_connection(self):
        db = SqliteExtDatabase(
            self.sqlite_db,
            pragmas={"foreign_keys": 1, "journal_mode": "wal", "cache_size": -64_000},
        )
        db_proxy.initialize(db)
        try:
            yield db
        finally:
            if not db.is_closed():
                db.close()

    def _get_db_stats(self, conn) -> Tuple[int, int, int]:
        count_query_map = {
            "all": "SELECT COUNT(DISTINCT r.id), MIN(r.id), MAX(r.id) "
                   "FROM regex_entity r JOIN regex_source_usage rsu ON r.id = rsu.regex_id",
            "internet": "SELECT COUNT(DISTINCT r.id), MIN(r.id), MAX(r.id) "
                        "FROM regex_entity r JOIN regex_source_usage rsu ON r.id = rsu.regex_id "
                        "JOIN project_spec p ON p.id = rsu.project_id "
                        "WHERE p.name IN ('RegExLib', 'Stack Overflow Posts', 'Stack Overflow Comments')",
            "oss": "SELECT COUNT(DISTINCT r.id), MIN(r.id), MAX(r.id) "
                   "FROM regex_entity r JOIN regex_source_usage rsu ON r.id = rsu.regex_id "
                   "JOIN project_spec p ON p.id = rsu.project_id "
                   "WHERE p.name NOT IN ('RegExLib', 'Stack Overflow Posts', 'Stack Overflow Comments')",
        }
        count, min_id, max_id = conn.execute(count_query_map[self.include_source]).fetchone()
        return count or 0, min_id or 0, max_id or 0

    def _fetch_all_regex_items(self) -> List[Tuple[int, str]]:
        conn = _get_db_connection(self.db_path)
        try:
            query = _build_partition_query(self.include_source)
            rows = conn.execute(query, (self.min_id, self.max_id)).fetchall()
            return [(r["id"], r["pattern"]) for r in rows if r["id"] not in SLOW_REGEX_IDS]
        finally:
            conn.close()

    def _create_count_partitions_from_items(
        self, regex_items: List[Tuple[int, str]]
    ) -> Tuple[List[Partition], List[Tuple[int, int]]]:
        total = len(regex_items)
        if self.num_partitions <= 0:
            return [], []
        chunk = math.ceil(total / self.num_partitions) if total else 0
        partitions: List[Partition] = []
        index_ranges: List[Tuple[int, int]] = []
        for i in range(self.num_partitions):
            start_idx = i * chunk
            end_idx = min(start_idx + chunk, total)
            if start_idx >= end_idx:
                partitions.append(Partition(start_id=0, end_id=0, partition_index=i))
                index_ranges.append((start_idx, end_idx))
                continue
            first_id = regex_items[start_idx][0]
            last_id = regex_items[end_idx - 1][0]
            partitions.append(Partition(start_id=first_id, end_id=last_id, partition_index=i))
            index_ranges.append((start_idx, end_idx))
        return partitions, index_ranges

    def query(
        self,
        ground_truth: str,
        positive_strings: List[str],
        negative_strings: List[str],
        targeted_pos_accuracy: float = 0.9,
        targeted_neg_accuracy: float = 0.85,
        timeout: Optional[float] = 0.005,
        limit: Optional[int] = None,
        collection_timeout: float = 300.0,  # retained for CLI parity (unused here),
        max_timeouts_per_regex: int = 3,
        max_wall_per_regex: float = 1.0,
    ) -> Tuple[Optional[RbeGenerationQuery], List[MatchResult]]:
        # Create or reuse the task/query rows the same way as in your Ray version
        with self._get_result_db_connection() as db:
            with db.atomic():
                task, _ = RbeGenerationTask.get_or_create(
                    ground_truth=ground_truth,
                    positive_examples=positive_strings,
                    negative_examples=negative_strings,
                )
                query_params = {
                    "source": self.include_source,
                    "targeted_pos_accuracy": targeted_pos_accuracy,
                    "targeted_neg_accuracy": targeted_neg_accuracy,
                    "timeout": timeout,
                    "collection_timeout": collection_timeout,
                    "limit": limit,
                    "experiment_id": self.experiment_id,
                }
                query, created = RbeGenerationQuery.get_or_create(
                    task=task, query_parameters=query_params, defaults={"status": "pending"}
                )
                if not created:
                    logger.info("Skipping query because it already exists")
                    return query, []

        t0 = time.time()
        # Normalize sets once in parent; copied to workers via initializer
        positive_strings = list({str(s) for s in positive_strings if s is not None})
        negative_strings = list({str(s) for s in negative_strings if s is not None})
        logger.info(f"Query with {len(positive_strings)} pos and {len(negative_strings)} neg strings")

        # 1) Fetch and partition by count (to avoid ID gaps and keep chunks balanced)
        all_items = self._fetch_all_regex_items()
        logger.info(f"Fetched {len(all_items)} regex items in total.")
        partitions, index_ranges = self._create_count_partitions_from_items(all_items)
        for i, (start_idx, end_idx) in enumerate(index_ranges):
            if start_idx < end_idx:
                first_id = all_items[start_idx][0]
                last_id = all_items[end_idx - 1][0]
                logger.info(f"Partition {i}: {end_idx - start_idx} items (IDs {first_id}..{last_id})")
            else:
                logger.info(f"Partition {i}: 0 items")

        # 2) Build work slices for the process pool (total_workers slices)
        total_workers = max(1, self.total_workers)
        slice_factor = max(8, min(32, len(all_items) // max(1, self.total_workers)))  # heuristic
        num_slices = max(self.total_workers * slice_factor, self.total_workers)
        slices = _split_into_n_slices(len(all_items), num_slices)

        tasks = [
            (all_items[s:e], targeted_pos_accuracy, targeted_neg_accuracy, timeout,
            max_timeouts_per_regex, max_wall_per_regex)
            for (s, e) in slices if s < e
        ]

        if not tasks:
            logger.info("No tasks to process (empty selection).")
            return query, []

        # 3) Process in parallel
        results: List[MatchResult] = []
        start_method = self.start_method  # allow override if desired
        # Prefer 'fork' on Unix for speed; 'spawn' is default on Windows
        ctx = get_context(start_method) if start_method else get_context()

        # Choose a reasonable chunksize to reduce IPC overhead if you have many slices
        map_chunksize = 1

        try:
            with ctx.Pool(
                processes=total_workers,
                initializer=_init_worker,
                initargs=(positive_strings, negative_strings),
                maxtasksperchild=self.maxtasks_per_child or None,
            ) as pool:
                for res_list in tqdm(
                    pool.imap_unordered(_worker_process_regexes, tasks, chunksize=map_chunksize),
                    total=len(tasks),
                    desc="Processing partitions",
                ):
                    if res_list:
                        results.extend(res_list)
        except KeyboardInterrupt:
            logger.warning("Interrupted by user.")
            raise

        # 4) Sort and limit like the Ray version
        results.sort(key=lambda x: (x.positive_accuracy + x.negative_accuracy), reverse=True)
        if limit:
            results = results[:limit]

        elapsed = time.time() - t0
        rate = (self.total_regexes / elapsed) if elapsed > 0 else 0.0
        logger.info(f"Processed {self.total_regexes:,} regexes in {elapsed:.2f}s ({rate:,.0f} regexes/s)")
        logger.info(f"Found {len(results)} candidates")
        return query, results


# --------------------------------------------------------------------------------------
# Persistence helpers (same as your Ray version)
# --------------------------------------------------------------------------------------
def init_db(db_path: str):
    db = SqliteExtDatabase(
        db_path, pragmas={"foreign_keys": 1, "journal_mode": "wal", "cache_size": -64_000}
    )
    db_proxy.initialize(db)


def drop_tables():
    db = db_proxy.obj
    with db.atomic():
        db.drop_tables([RbeGenerationTask, RbeGenerationQuery, RbeGeneratedCandidate])


def create_schema_if_needed():
    db = db_proxy.obj
    db.create_tables([RbeGenerationTask, RbeGenerationQuery, RbeGeneratedCandidate], safe=True)


def insert_rbe_generated_candidates(
    query: RbeGenerationQuery,
    results: List[MatchResult],
    ground_truth: str,
    num_pos_strings: int,
    num_neg_strings: int,
    generation_time: float,
):
    """Calculates accuracy from results and performs a bulk insert."""
    if not results:
        return

    candidates_to_insert = []
    total_strings = num_pos_strings + num_neg_strings
    if total_strings == 0:
        return

    for r in results:
        if r.pattern == ground_truth:
            continue
        true_positives = r.positive_matches
        true_negatives = num_neg_strings - r.negative_matches
        accuracy = (true_positives + true_negatives) / total_strings

        candidates_to_insert.append({
            "query": query,
            "regex_pattern": r.pattern,
            "accuracy": accuracy,
            "generation_time": generation_time,
        })

    if candidates_to_insert:
        db = db_proxy.obj
        with db.atomic():
            RbeGeneratedCandidate.insert_many(candidates_to_insert).execute()


# --------------------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------------------
def query_rbe(
    matcher: MPRegexMatcher,
    positive_strings: List[str],
    negative_strings: List[str],
    targeted_pos_accuracy: float,
    targeted_neg_accuracy: float,
    regex_matching_timeout: float,
    collection_timeout: float,
    limit: Optional[int],
    max_timeouts_per_regex: int,
    max_wall_per_regex: float,
    ground_truth: Optional[str] = None,
):
    query, results = None, []
    try:
        start_time = time.perf_counter()
        query, results = matcher.query(
            ground_truth=ground_truth,
            positive_strings=positive_strings,
            negative_strings=negative_strings,
            targeted_pos_accuracy=targeted_pos_accuracy,
            targeted_neg_accuracy=targeted_neg_accuracy,
            timeout=regex_matching_timeout,
            limit=limit,
            collection_timeout=collection_timeout,
            max_timeouts_per_regex=max_timeouts_per_regex,
            max_wall_per_regex=max_wall_per_regex,
        )
        generation_time = round(time.perf_counter() - start_time, 3)

        if query:
            insert_rbe_generated_candidates(
                query, results, ground_truth,
                len(positive_strings), len(negative_strings),
                generation_time,
            )
            query.status = "success" if results else "solution_not_found"
            query.save()
        return results

    except Exception as e:
        logger.exception("query_rbe failed")
        if query:
            query.status = "error"
            query.save()
        raise e


def process_ndjson_file(matcher: MPRegexMatcher, ndjson_path: str, **kwargs):
    with open(ndjson_path, "r") as f:
        lines = f.readlines()
    for line in tqdm(lines, desc="Processing Queries"):
        data = orjson.loads(line)
        query_rbe(
            matcher=matcher,
            positive_strings=[s.get("subject") for s in data.get("positive_strings", [])],
            negative_strings=[s.get("subject") for s in data.get("negative_strings", [])],
            ground_truth=data.get("regex"),
            **kwargs,
        )


# --------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------
def build_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Query RBE (mrab-regex) with multiprocessing against a regex DB.")
    p.add_argument("--input-file", required=True)
    p.add_argument("--rbe-db", required=True)
    p.add_argument("--sqlite-db", required=True)

    p.add_argument("--num-partitions", type=int, default=4, help="Logical partitions (used to compute total workers).")
    p.add_argument("--workers-per-partition", type=int, default=9, help="Total processes = partitions * workers per partition.")

    p.add_argument("--regex-matching-timeout", type=float, default=0.01)
    p.add_argument("--collection-timeout", type=float, default=300.0)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--targeted-pos-accuracy", type=float, default=1.0)
    p.add_argument("--targeted-neg-accuracy", type=float, default=1.0)
    p.add_argument("--drop-tables", action="store_true")
    p.add_argument("--no-progress", action="store_true")
    p.add_argument("--include-source", type=str, default="all", choices=["all", "internet", "oss"])
    p.add_argument("--experiment-id", type=str, default=None)
    # --- add CLI flags (optional defaults shown) ---
    p.add_argument("--max-timeouts-per-regex", type=int, default=3,
                help="Skip a regex after this many match timeouts across pos+neg.")
    p.add_argument("--max-wall-per-regex", type=float, default=1.0,
                help="Skip a regex after this many seconds of wall-clock across pos+neg.")

    # MP-specific tuning knobs (optional)
    p.add_argument("--start-method", type=str, default=None, choices=[None, "fork", "spawn", "forkserver"], help="Process start method override.")
    p.add_argument("--maxtasks-per-child", type=int, default=0, help="Recycle worker after N tasks (0 = unlimited).")
    return p.parse_args()


def main():
    args = build_args()

    init_db(args.sqlite_db)
    if args.drop_tables:
        logger.warning("Dropping result tables...")
        drop_tables()
    create_schema_if_needed()

    matcher = MPRegexMatcher(
        db_path=args.rbe_db,
        sqlite_db=args.sqlite_db,
        num_partitions=args.num_partitions,
        workers_per_partition=args.workers_per_partition,
        include_source=args.include_source,
        read_only=True,
        experiment_id=args.experiment_id,
        start_method=args.start_method,
        maxtasks_per_child=args.maxtasks_per_child,
    )

    try:
        process_ndjson_file(
            matcher=matcher,
            ndjson_path=args.input_file,
            targeted_pos_accuracy=args.targeted_pos_accuracy,
            targeted_neg_accuracy=args.targeted_neg_accuracy,
            regex_matching_timeout=args.regex_matching_timeout,
            collection_timeout=args.collection_timeout,
            limit=args.limit,
            max_timeouts_per_regex=args.max_timeouts_per_regex,
            max_wall_per_regex=args.max_wall_per_regex,
        )
    finally:
        logger.info("Processing complete.")


if __name__ == "__main__":
    main()
