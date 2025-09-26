#!/usr/bin/env python3
# metrics/calculate_metrics.py
#
# Populates CandidateRegexMetric with computed metrics (pattern_length, distinct_features, syntactic_similarity)
# and supports a --ground-truth mode to populate GroundTruthMetric (pattern_length, distinct_features).
#
# Ground-truth mode:
#   - Selects DISTINCT tasks from the chosen source (rbe/llm/synth) that have at least one query
#     whose query_parameters["experiment_id"] contains --experiment-id (substring).
#   - Computes BOTH GT metrics for each task (fast).
#   - UPSERTS into ground_truth_metrics; on conflict updates ONLY the selected metric column
#     (so you can choose which to refresh via --metric).
#
# Candidate mode:
#   - Filters candidates by experiment_id substring on their parent query.
#   - Skips rows where the selected metric is already non-NULL.
#   - Computes metric in parallel and writes via bulk update/insert.

import argparse
import sys
from dataclasses import dataclass
from multiprocessing import Pool, cpu_count
from typing import Dict, Iterable, Iterator, List, Tuple
from contextlib import contextmanager
import signal

from peewee import Case, fn, EXCLUDED
from playhouse.sqlite_ext import JSONField, SqliteExtDatabase, JSONPath

# Helpers
from metrics.count_distinct_features import count_distinct_features
from metrics.syntactic_similarity.distance import regex_ast_distance
from metrics.strictness_score.strictness_score2 import get_candidate_regex_automaton_size
from metrics.semantic_similarity.regex_semantic_sim import symmetrical_semantic_similarity

# tqdm (fallback to no-op if unavailable)
try:
    from tqdm.auto import tqdm
except Exception:  # pragma: no cover
    class tqdm:  # type: ignore
        def __init__(self, iterable=None, total=None, desc=None, unit=None):
            self.iterable = iterable
            self.total = total
        def update(self, n=1): pass
        def close(self): pass
        def __iter__(self):
            if self.iterable is None: return iter(())
            return iter(self.iterable)

# Peewee models (ensure GroundTruthMetric exists in your models)
from regex_generation.db.models import (
    db_proxy,
    RbeGenerationTask, RbeGenerationQuery, RbeGeneratedCandidate,
    LlmGenerationTask, LlmGenerationQuery, LlmGeneratedCandidate,
    SynthesizerGenerationTask, SynthesizerGenerationQuery, SynthesizerGeneratedCandidate,
    CandidateRegexMetric,
    GroundTruthMetric,
)

# ----------------------------- Metric implementations -----------------------------

def metric_pattern_length(pattern: str) -> int:
    return len(pattern or "")

def metric_distinct_features(pattern: str) -> int | None:
    """Count the number of distinct regex feature types (fast heuristic)."""
    if not pattern:
        return 0
    count, _ = count_distinct_features(pattern)
    if count == 0: return None
    return count

def metric_syntactic_similarity(pattern: str, ground_truth: str, timeout_s: int) -> Dict[str, object]:
    """
    Calls regex_ast_distance(pattern, ground_truth) with per-item timeout.
    Stores JSON in CandidateRegexMetric.syntactic_similarity:
      {"ast_edit_distance": <float|null>, "normalized_ast_edit_distance": <float|null>, "status": "success|timeout|error"}
    """
    if not pattern or not ground_truth:
        return {"ast_edit_distance": None, "normalized_ast_edit_distance": None, "status": "error"}

    @contextmanager
    def time_limit(seconds: int):
        if seconds and hasattr(signal, "SIGALRM"):
            def _raise_timeout(signum, frame):  # noqa: ARG001
                raise TimeoutError("metric timeout")
            old = signal.signal(signal.SIGALRM, _raise_timeout)
            signal.alarm(seconds)
            try:
                yield
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old)
        else:
            yield

    try:
        with time_limit(timeout_s):
            out = regex_ast_distance(pattern, ground_truth)
    except TimeoutError:
        return {"ast_edit_distance": None, "normalized_ast_edit_distance": None, "status": "timeout"}
    except Exception:
        return {"ast_edit_distance": None, "normalized_ast_edit_distance": None, "status": "error"}

    d = out.get("ast_edit_distance")
    nd = out.get("normalized_ast_edit_distance")
    status = "success" if (d is not None and nd is not None) else "error"
    return {"ast_edit_distance": d, "normalized_ast_edit_distance": nd, "status": status}

def metric_automaton_size(pattern: str, timeout_s: int, approximate: bool = True) -> Dict[str, object]:
    """
    Compute automaton size for a regex pattern with timeout.
    Returns: {"automaton_size": <int|null>, "status": "success"|"timeout"|"error"}
    """
    if not pattern:
        return {"automaton_size": None, "status": "error"}

    from contextlib import contextmanager
    import signal

    @contextmanager
    def time_limit(seconds: int):
        if seconds and hasattr(signal, "SIGALRM"):
            def _raise_timeout(signum, frame):  # noqa: ARG001
                raise TimeoutError("metric timeout")
            old = signal.signal(signal.SIGALRM, _raise_timeout)
            signal.alarm(seconds)
            try:
                yield
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old)
        else:
            yield

    try:
        with time_limit(timeout_s):
            sz = get_candidate_regex_automaton_size(pattern, approximate=True)
    except TimeoutError:
        return {"automaton_size": None, "status": "timeout"}
    except Exception:
        return {"automaton_size": None, "status": "error"}

    return {"automaton_size": int(sz) if sz is not None else None, "status": "success"}

def metric_semantic_similarity(pattern: str, ground_truth: str, timeout: int,
                               base_substring: str = "evil", beta: float = 1.0) -> Dict[str, object]:
    """
    Run symmetrical_semantic_similarity with a POSIX alarm timeout.
    Never pass a 'timeout' kwarg to the underlying function.
    """
    if not pattern or not ground_truth:
        return {"status": "error"}

    from contextlib import contextmanager
    import signal

    @contextmanager
    def time_limit(seconds: int):
        if seconds and hasattr(signal, "SIGALRM"):
            def _raise_timeout(signum, frame):  # noqa: ARG001
                raise TimeoutError("metric timeout")
            old = signal.signal(signal.SIGALRM, _raise_timeout)
            signal.alarm(seconds)
            try:
                yield
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old)
        else:
            yield

    try:
        with time_limit(timeout):
            # DO NOT pass timeout=... here; the function doesn't accept it.
            out = symmetrical_semantic_similarity(
                pattern, ground_truth, base_substring=base_substring, beta=beta, debug=False
            )
    except TimeoutError:
        return {"status": "timeout"}
    except Exception as e:
        print(f"Error in metric_semantic_similarity: {e}")
        # traceback.print_exc()
        return {"status": "error"}

    # Ensure status is present
    if isinstance(out, dict):
        return {**out, "status": "success"}
    return {"value": out, "status": "success"}


# ----------------------------- Metric registry (candidates) -----------------------------

METRICS_SCALAR = {
    "pattern_length": metric_pattern_length,
    "distinct_features": metric_distinct_features,
}

METRIC_JSON_NEEDS_GT = {
    "syntactic_similarity": metric_syntactic_similarity,
    "semantic_similarity": metric_semantic_similarity,
}

METRIC_JSON = {
    "automaton_size": metric_automaton_size,
}

FIELD_BY_METRIC = {
    "pattern_length": CandidateRegexMetric.pattern_length,
    "distinct_features": CandidateRegexMetric.distinct_features,
    "syntactic_similarity": CandidateRegexMetric.syntactic_similarity,
    "automaton_size": CandidateRegexMetric.automaton_size,
    "semantic_similarity": CandidateRegexMetric.semantic_similarity,
}

# ----------------------------- Helpers -----------------------------

@dataclass(frozen=True)
class SourceSpec:
    task_model: type
    query_model: type
    cand_model: type
    fk_field: object
    null_fields: Dict[object, None]

def get_source_spec(kind: str) -> SourceSpec:
    if kind == "rbe":
        return SourceSpec(
            task_model=RbeGenerationTask,
            query_model=RbeGenerationQuery,
            cand_model=RbeGeneratedCandidate,
            fk_field=CandidateRegexMetric.rbe_candidate,
            null_fields={
                CandidateRegexMetric.llm_candidate: None,
                CandidateRegexMetric.synthesizer_candidate: None,
            },
        )
    if kind == "llm":
        return SourceSpec(
            task_model=LlmGenerationTask,
            query_model=LlmGenerationQuery,
            cand_model=LlmGeneratedCandidate,
            fk_field=CandidateRegexMetric.llm_candidate,
            null_fields={
                CandidateRegexMetric.rbe_candidate: None,
                CandidateRegexMetric.synthesizer_candidate: None,
            },
        )
    if kind == "synth":
        return SourceSpec(
            task_model=SynthesizerGenerationTask,
            query_model=SynthesizerGenerationQuery,
            cand_model=SynthesizerGeneratedCandidate,
            fk_field=CandidateRegexMetric.synthesizer_candidate,
            null_fields={
                CandidateRegexMetric.rbe_candidate: None,
                CandidateRegexMetric.llm_candidate: None,
            },
        )
    raise ValueError(f"Unknown type: {kind}")

def contains_experiment_id_subq(QueryModel, experiment_id: str):
    """Substring match on JSON $.experiment_id using JSONPath + INSTR()."""
    jp = JSONPath('$.experiment_id')
    return (QueryModel
            .select(QueryModel.id)
            .where(fn.instr(fn.json_extract(QueryModel.query_parameters, jp),
                            str(experiment_id)) > 0))

def computed_ids_subq(fk_field, metric_field):
    """Candidates that already have a non-NULL value for the selected metric."""
    if fk_field is CandidateRegexMetric.rbe_candidate:
        return (CandidateRegexMetric
                .select(CandidateRegexMetric.rbe_candidate)
                .where((CandidateRegexMetric.rbe_candidate.is_null(False)) &
                       (metric_field.is_null(False))))
    if fk_field is CandidateRegexMetric.llm_candidate:
        return (CandidateRegexMetric
                .select(CandidateRegexMetric.llm_candidate)
                .where((CandidateRegexMetric.llm_candidate.is_null(False)) &
                       (metric_field.is_null(False))))
    return (CandidateRegexMetric
            .select(CandidateRegexMetric.synthesizer_candidate)
            .where((CandidateRegexMetric.synthesizer_candidate.is_null(False)) &
                   (metric_field.is_null(False))))

def iter_candidates_scalar(CandModel, QueryModel, queries_subq, already_done_subq) -> Iterator[Tuple[str, str]]:
    """(candidate_id, pattern) for scalar metrics."""
    return (CandModel
            .select(CandModel.id, CandModel.regex_pattern)
            .where(
                (CandModel.query.in_(queries_subq)) &
                (CandModel.id.not_in(already_done_subq))
            )
            .tuples()
            .iterator())

def iter_candidates_with_gt(CandModel, QueryModel, queries_subq, already_done_subq) -> Iterator[Tuple[str, str, str]]:
    """(candidate_id, pattern, ground_truth) for metrics that require ground truth."""
    TaskModel = QueryModel.task.rel_model
    q = (CandModel
         .select(CandModel.id,
                 CandModel.regex_pattern,
                 TaskModel.ground_truth.alias('gt'))
         .join(QueryModel, on=(CandModel.query == QueryModel.id))
         .join(TaskModel, on=(QueryModel.task == TaskModel.id))
         .where(
             (CandModel.query.in_(queries_subq)) &
             (CandModel.id.not_in(already_done_subq))
         )
         .tuples())
    return q.iterator()

def batched(iterable: Iterable, n: int) -> Iterable[List]:
    batch = []
    for x in iterable:
        batch.append(x)
        if len(batch) >= n:
            yield batch
            batch = []
    if batch:
        yield batch

# ------- Candidate upsert helpers (JSON-safe CASE updates) -------

_UPDATE_CASE_LIMIT = 250
_INSERT_ROWS_LIMIT = 300
_IN_LOOKUP_LIMIT   = 900

def fetch_existing_metric_ids_for_candidates(fk_field, candidate_ids: List[str]) -> Dict[str, str]:
    """
    Return {candidate_id -> metric_row_id} for rows that already exist for this type.
    """
    mapping: Dict[str, str] = {}
    if not candidate_ids:
        return mapping
    for chunk in batched(candidate_ids, _IN_LOOKUP_LIMIT):
        q = (CandidateRegexMetric
             .select(CandidateRegexMetric.id, fk_field.alias('fk'))
             .where(fk_field.in_(chunk)))
        for row in q.dicts():
            cid = row['fk']
            if cid and cid not in mapping:
                mapping[cid] = row['id']
    return mapping

def bulk_update_metric(metric_field, id_value_pairs: List[Tuple[str, object]]):
    """
    Update metric_field for many rows using a single CASE per chunk.
    IMPORTANT: If metric_field is JSONField, pre-serialize dicts with db_value()
    before embedding them in CASE, or SQLite will see raw Python dicts.
    """
    if not id_value_pairs:
        return 0

    is_json = isinstance(metric_field, JSONField)
    updated = 0

    for chunk in batched(id_value_pairs, _UPDATE_CASE_LIMIT):
        # Pre-coerce JSON values so they bind as TEXT.
        if is_json:
            coerced = [(rid, metric_field.db_value(val)) for rid, val in chunk]
        else:
            coerced = chunk

        ids = [rid for rid, _ in coerced]
        case_expr = Case(CandidateRegexMetric.id,
                         [(rid, val) for rid, val in coerced],
                         None)
        (CandidateRegexMetric
         .update({metric_field: case_expr})
         .where(CandidateRegexMetric.id.in_(ids))
         .execute())
        updated += len(coerced)

    return updated

def bulk_insert_metric(spec: SourceSpec, metric_field, cid_value_pairs: List[Tuple[str, object]]):
    """
    Insert metric rows for candidates that do not yet have a row.
    For JSONField, insert_many() handles dicts fine, but we also pre-coerce to
    be consistent (and to avoid edge cases with some drivers).
    """
    if not cid_value_pairs:
        return 0

    is_json = isinstance(metric_field, JSONField)
    inserted = 0

    for chunk in batched(cid_value_pairs, _INSERT_ROWS_LIMIT):
        if is_json:
            rows = [
                {spec.fk_field: cid, **spec.null_fields, metric_field: metric_field.db_value(val)}
                for (cid, val) in chunk
            ]
        else:
            rows = [
                {spec.fk_field: cid, **spec.null_fields, metric_field: val}
                for (cid, val) in chunk
            ]

        CandidateRegexMetric.insert_many(rows).execute()
        inserted += len(chunk)

    return inserted

# ----------------------------- Ground-truth mode -----------------------------

def iter_ground_truth_tasks(spec: SourceSpec, experiment_id: str) -> List[Tuple[str, object, object]]:
    """
    DISTINCT tasks (gt, pos, neg) for which there exists a query whose
    query_parameters['experiment_id'] contains experiment_id.
    """
    QueryModel = spec.query_model
    TaskModel = spec.task_model
    jp = JSONPath('$.experiment_id')
    q = (TaskModel
         .select(TaskModel.ground_truth, TaskModel.positive_examples, TaskModel.negative_examples)
         .join(QueryModel, on=(QueryModel.task == TaskModel.id))
         .where(fn.instr(fn.json_extract(QueryModel.query_parameters, jp), str(experiment_id)) > 0)
         .where(TaskModel.ground_truth.is_null(False))
         .distinct())
    return list(q.tuples())

def compute_ground_truth_worker_both(item: Tuple[str, object, object]) -> Dict[str, object]:
    """Compute BOTH GT metrics for robust upsert."""
    gt, pos, neg = item
    return {
        "ground_truth": gt,
        "positive_examples": pos,
        "negative_examples": neg,
        "pattern_length": metric_pattern_length(gt),
        "distinct_features": metric_distinct_features(gt),
    }

# NEW worker for GT rows
def compute_ground_truth_worker_gt(item: Tuple[str, object, object]) -> Dict[str, object]:
    """
    Ground-truth worker: always computes the two int metrics for insert validity,
    and conditionally adds automaton_size JSON when requested.
    """
    gt, pos, neg = item
    row = {
        "ground_truth": gt,
        "positive_examples": pos,
        "negative_examples": neg,
        "pattern_length": metric_pattern_length(gt),
        "distinct_features": metric_distinct_features(gt),
    }
    if _GT_SELECTED_METRIC == "automaton_size":
        row["automaton_size"] = metric_automaton_size(gt, _TIMEOUT_SECS)
    return row

def upsert_ground_truth(rows: List[Dict[str, object]], selected_metric: str) -> int:
    """
    Upsert into GroundTruthMetric on UNIQUE(ground_truth, positive_examples, negative_examples).
    On conflict, update ONLY the selected metric column.
    On insert, both metrics are provided.
    """
    if not rows:
        return 0

    if selected_metric not in ("pattern_length", "distinct_features", "automaton_size"):
        raise ValueError("selected_metric must be 'pattern_length' or 'distinct_features'")

    if selected_metric == "pattern_length":
        field_to_update = GroundTruthMetric.pattern_length
    elif selected_metric == "distinct_features":
        field_to_update = GroundTruthMetric.distinct_features
    else:  # "automaton_size"
        field_to_update = GroundTruthMetric.automaton_size  # <-- JSONField

    pe_field: JSONField = GroundTruthMetric.positive_examples
    ne_field: JSONField = GroundTruthMetric.negative_examples

    total = 0
    for chunk in batched(rows, 300):  # safe wrt SQLite's param limit
        # Coerce JSON to TEXT for consistent equality/binding
        for r in chunk:
            r[pe_field] = pe_field.db_value(r.pop("positive_examples"))
            r[ne_field] = ne_field.db_value(r.pop("negative_examples"))
            # ground_truth, pattern_length, distinct_features remain as-is (ints/str)

        (GroundTruthMetric
        .insert_many(chunk)
        .on_conflict(
            conflict_target=[
                GroundTruthMetric.ground_truth,
                GroundTruthMetric.positive_examples,
                GroundTruthMetric.negative_examples,
            ],
            update={field_to_update: EXCLUDED[field_to_update.name]},  # works for JSON/int
        )
        .execute())
        total += len(chunk)
    return total

# ----------------------------- Workers (candidates) -----------------------------

_SELECTED_METRIC_NAME = None
_TIMEOUT_SECS = 5
_GT_SELECTED_METRIC = None

def compute_metric_worker_scalar(item: Tuple[str, str]) -> Tuple[str, object]:
    cid, pattern = item
    fn_metric = METRICS_SCALAR[_SELECTED_METRIC_NAME]  # type: ignore
    return cid, fn_metric(pattern)

def compute_metric_worker_json_needs_gt(item: Tuple[str, str, str]) -> Tuple[str, object]:
    cid, pattern, gt = item
    fn_metric = METRIC_JSON_NEEDS_GT[_SELECTED_METRIC_NAME]  # includes "semantic_similarity"
    return cid, fn_metric(pattern, gt, _TIMEOUT_SECS)  # <-- positional timeout, not timeout=...

def compute_metric_worker_json(item: Tuple[str, str]) -> Tuple[str, object]:
    cid, pattern = item
    fn_metric = METRIC_JSON[_SELECTED_METRIC_NAME]  # type: ignore
    return cid, fn_metric(pattern, _TIMEOUT_SECS)

# ----------------------------- CLI / Pipeline -----------------------------

def create_schema_if_needed():
    db = db_proxy.obj
    db.create_tables([CandidateRegexMetric, GroundTruthMetric])

def main():
    parser = argparse.ArgumentParser(description="Compute and store regex metrics.")
    parser.add_argument("--db-path", required=True, help="Path to SQLite database file.")
    parser.add_argument("--type", required=True, choices=["rbe", "synth", "llm"],
                        help="Source type.")
    parser.add_argument("--experiment-id", required=True,
                        help="Substring to match in query_parameters['experiment_id'].")
    parser.add_argument(
        "--metric",
        required=True,
        choices=sorted(list(METRICS_SCALAR.keys()) + list(METRIC_JSON.keys()) + list(METRIC_JSON_NEEDS_GT.keys())),
        help="Which metric to compute (exactly one). For --ground-truth, choose: pattern_length or distinct_features."
    )
    parser.add_argument("--timeout-seconds", type=int, default=5,
                        help="Per-item timeout for expensive metrics (syntactic_similarity). 0 disables.")
    parser.add_argument("--num-workers", type=int, default=max(1, cpu_count() - 1),
                        help="Worker processes (default: CPUs-1).")
    parser.add_argument("--batch-size", type=int, default=2000,
                        help="Rows per DB batch (default: 2000).")
    parser.add_argument("--ground-truth", action="store_true",
                        help="Operate on tasks and upsert into GroundTruthMetric.")
    args = parser.parse_args()

    pragmas = (
        ("journal_mode", "wal"),
        ("synchronous", 1),         # NORMAL
        ("cache_size", -64 * 1024), # 64MB
        ("foreign_keys", 1),
        ("temp_store", 2),
    )
    db = SqliteExtDatabase(args.db_path, pragmas=pragmas, check_same_thread=False)
    db_proxy.initialize(db)
    create_schema_if_needed()

    spec = get_source_spec(args.type)

    # Build inputs
    global _SELECTED_METRIC_NAME, _TIMEOUT_SECS, _GT_SELECTED_METRIC
    _GT_SELECTED_METRIC = args.metric
    _SELECTED_METRIC_NAME = args.metric
    _TIMEOUT_SECS = max(0, int(args.timeout_seconds))

    # -------- Ground-truth mode --------
    if args.ground_truth:
        if args.metric not in ("pattern_length", "distinct_features", "automaton_size"):  # <-- add automaton_size
            parser.error("--ground-truth supports --metric: pattern_length, distinct_features, automaton_size.")

        selected_metric = args.metric
        tasks = iter_ground_truth_tasks(spec, args.experiment_id)
        total = len(tasks)
        if total == 0:
            print("[OK][GT] nothing to do")
            return 0

        rows: List[Dict[str, object]] = []
        with Pool(processes=args.num_workers) as pool:
            pbar = tqdm(total=total, desc=f"Ground truth ({args.type})", unit="task")
            try:
                for batch in batched(
                        pool.imap_unordered(compute_ground_truth_worker_gt, tasks, chunksize=2000),
                        args.batch_size):
                    rows.extend(batch)
                    pbar.update(len(batch))
            finally:
                pbar.close()

        written = upsert_ground_truth(rows, selected_metric)
        print(f"[OK][GT] tasks_processed={total} upserted={written} type={args.type} experiment_id={args.experiment_id} metric={selected_metric}")
        return 0

    # -------- Candidate metrics mode --------
    metric_name = args.metric
    metric_field = FIELD_BY_METRIC[metric_name]

    # Build subqueries
    queries_subq = contains_experiment_id_subq(spec.query_model, args.experiment_id)
    already_done = computed_ids_subq(spec.fk_field, metric_field)

    if metric_name in METRICS_SCALAR:
        items = list(iter_candidates_scalar(spec.cand_model, spec.query_model, queries_subq, already_done))
        worker = compute_metric_worker_scalar
    elif metric_name in METRIC_JSON:
        items = list(iter_candidates_scalar(spec.cand_model, spec.query_model, queries_subq, already_done))
        worker = compute_metric_worker_json
    else:  # METRIC_JSON_NEEDS_GT (e.g., syntactic_similarity)
        items = list(iter_candidates_with_gt(spec.cand_model, spec.query_model, queries_subq, already_done))
        worker = compute_metric_worker_json_needs_gt

    total = len(items)
    processed = updated = inserted = 0

    with Pool(processes=args.num_workers) as pool:
        pbar = tqdm(total=total, desc=f"Computing {metric_name}", unit="cand")
        try:
            for result_batch in batched(pool.imap_unordered(worker, items, chunksize=2000),
                                        args.batch_size):
                processed += len(result_batch)
                pbar.update(len(result_batch))

                cids = [cid for cid, _ in result_batch]
                existing_map = fetch_existing_metric_ids_for_candidates(spec.fk_field, cids)

                to_update = [(existing_map[cid], val) for (cid, val) in result_batch if cid in existing_map]
                to_insert = [(cid, val) for (cid, val) in result_batch if cid not in existing_map]

                # Commit per batch so progress survives interruptions
                if to_update:
                    with db.atomic():
                        updated += bulk_update_metric(metric_field, to_update)
                if to_insert:
                    with db.atomic():
                        inserted += bulk_insert_metric(spec, metric_field, to_insert)

        except KeyboardInterrupt:
            pbar.close()
            # Kill workers so we don't hang
            pool.terminate()
            pool.join()
            print(f"[INTERRUPTED] partial save complete: processed={processed} updated={updated} inserted={inserted}")
            return 130  # conventional exit code for SIGINT
        finally:
            pbar.close()

    print(f"[OK] processed={processed} updated={updated} inserted={inserted} "
          f"type={args.type} experiment_id={args.experiment_id} metric={metric_name} "
          f"timeout={_TIMEOUT_SECS}s")
    return 0

if __name__ == "__main__":
    sys.exit(main())
