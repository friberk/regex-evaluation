#!/usr/bin/env python3
import argparse
import json
import sqlite3
from typing import Iterable, Dict, Any

# Delimiters used in fallback (non-JSON1) mode
SEP = "\x1f"       # char(31): item separator
KV_SEP = "\x1e"    # char(30): field separator for project items
STR_FSEP = "\x1d"  # char(29): field separator for string items


def has_json1(conn: sqlite3.Connection) -> bool:
    try:
        conn.execute("SELECT json('[]')").fetchone()
        conn.execute("SELECT json_group_array(1)").fetchone()
        return True
    except sqlite3.DatabaseError:
        return False


def iter_rows_json1(conn: sqlite3.Connection) -> Iterable[Dict[str, Any]]:
    """
    JSON1-enabled path:
      - projects: JSON array of {"id","name","repo"} aggregated per regex_id
      - positive_strings / negative_strings: JSON arrays of objects with full fields per test_suite_id
    """
    # sql = """
    # WITH
    # rp AS (  -- All projects that have a test suite for a given regex_id
    #   SELECT DISTINCT ts.regex_id, ts.project_id
    #   FROM test_suite AS ts
    # ),
    # project_groups AS (
    #   SELECT
    #     rp.regex_id,
    #     json_group_array(json_object('id', p.id, 'name', p.name, 'repo', p.repo)) AS projects
    #   FROM rp
    #   JOIN project_spec AS p ON p.id = rp.project_id
    #   GROUP BY rp.regex_id
    # ),
    # suite_strings AS (
    #   SELECT
    #     tss.test_suite_id,
    #     json_group_array(
    #       json_object(
    #         'id', tss.id,
    #         'subject', tss.subject,
    #         'func', tss.func,
    #         'full_match', tss.full_match,
    #         'partial_match', tss.partial_match,
    #         'first_sub_match_start', tss.first_sub_match_start,
    #         'first_sub_match_end', tss.first_sub_match_end
    #       )
    #     ) FILTER (WHERE tss.full_match = 1 OR tss.partial_match = 1) AS positive_strings,
    #     json_group_array(
    #       json_object(
    #         'id', tss.id,
    #         'subject', tss.subject,
    #         'func', tss.func,
    #         'full_match', tss.full_match,
    #         'partial_match', tss.partial_match,
    #         'first_sub_match_start', tss.first_sub_match_start,
    #         'first_sub_match_end', tss.first_sub_match_end
    #       )
    #     ) FILTER (WHERE IFNULL(tss.full_match,0) = 0 AND IFNULL(tss.partial_match,0) = 0) AS negative_strings
    #   FROM test_suite_string AS tss
    #   GROUP BY tss.test_suite_id
    # )
    # SELECT
    #   ts.id AS test_suite_id,
    #   r.pattern AS regex,
    #   pg.projects,
    #   ss.positive_strings,
    #   ss.negative_strings
    # FROM test_suite AS ts
    # JOIN regex_entity    AS r  ON r.id = ts.regex_id
    # JOIN project_groups  AS pg ON pg.regex_id = ts.regex_id
    # JOIN suite_strings   AS ss ON ss.test_suite_id = ts.id
    # """
    sql = """
    WITH suite_strings AS (
      SELECT
        tss.test_suite_id,
        json_group_array(
          json_object(
            'id', tss.id,
            'subject', tss.subject,
            'func', tss.func,
            'full_match', tss.full_match,
            'partial_match', tss.partial_match,
            'first_sub_match_start', tss.first_sub_match_start,
            'first_sub_match_end', tss.first_sub_match_end
          )
        ) FILTER (WHERE tss.full_match = 1 OR tss.partial_match = 1) AS positive_strings,
        json_group_array(
          json_object(
            'id', tss.id,
            'subject', tss.subject,
            'func', tss.func,
            'full_match', tss.full_match,
            'partial_match', tss.partial_match,
            'first_sub_match_start', tss.first_sub_match_start,
            'first_sub_match_end', tss.first_sub_match_end
          )
        ) FILTER (WHERE IFNULL(tss.full_match,0) = 0 AND IFNULL(tss.partial_match,0) = 0) AS negative_strings
      FROM test_suite_string AS tss
      GROUP BY tss.test_suite_id
    )
    SELECT
      ts.id AS test_suite_id,
      r.pattern AS regex,
      json_object('id', p.id, 'name', p.name, 'repo', p.repo) AS project,
      ss.positive_strings,
      ss.negative_strings
    FROM test_suite AS ts
    LEFT JOIN suite_strings AS ss ON ss.test_suite_id = ts.id
    JOIN regex_entity  AS r ON r.id = ts.regex_id
    JOIN project_spec  AS p ON p.id = ts.project_id
    ORDER BY ts.id;
    """
    cur = conn.execute(sql)
    for test_suite_id, regex, project, positive_strings, negative_strings in cur:
        yield {
            "test_suite_id": test_suite_id,
            "regex": regex,
            # "projects": json.loads(projects_json) if projects_json else [],
            "project": json.loads(project) if project else {},
            "positive_strings": json.loads(positive_strings) if positive_strings else [],
            "negative_strings": json.loads(negative_strings) if negative_strings else [],
        }


def iter_rows_concat(conn: sqlite3.Connection) -> Iterable[Dict[str, Any]]:
    """
    Fallback path without JSON1:
      - projects_gc: items "id<KV_SEP>name<KV_SEP>repo" joined by SEP
      - pos_gc / neg_gc: items with 7 fields joined by STR_FSEP, items joined by SEP
                         fields: id,subject,func,full_match,partial_match,first_sub_match_start,first_sub_match_end
    """
    sql = f"""
    WITH
    rp AS (
      SELECT DISTINCT ts.regex_id, ts.project_id
      FROM test_suite AS ts
    ),
    project_groups AS (
      SELECT
        rp.regex_id,
        group_concat(p.id || char(30) || p.name || char(30) || p.repo, char(31)) AS projects_gc
      FROM rp
      JOIN project_spec AS p ON p.id = rp.project_id
      GROUP BY rp.regex_id
    ),
    suite_strings AS (
      SELECT
        tss.test_suite_id,
        group_concat(
          CASE WHEN (tss.full_match = 1 OR tss.partial_match = 1) THEN
            tss.id || char(29) ||
            IFNULL(tss.subject, '') || char(29) ||
            IFNULL(tss.func, '') || char(29) ||
            IFNULL(tss.full_match, 0) || char(29) ||
            IFNULL(tss.partial_match, 0) || char(29) ||
            IFNULL(tss.first_sub_match_start, -1) || char(29) ||
            IFNULL(tss.first_sub_match_end, -1)
          END, char(31)
        ) AS pos_gc,
        group_concat(
          CASE WHEN IFNULL(tss.full_match, 0) = 0 AND IFNULL(tss.partial_match, 0) = 0 THEN
            tss.id || char(29) ||
            IFNULL(tss.subject, '') || char(29) ||
            IFNULL(tss.func, '') || char(29) ||
            IFNULL(tss.full_match, 0) || char(29) ||
            IFNULL(tss.partial_match, 0) || char(29) ||
            IFNULL(tss.first_sub_match_start, -1) || char(29) ||
            IFNULL(tss.first_sub_match_end, -1)
          END, char(31)
        ) AS neg_gc
      FROM test_suite_string AS tss
      GROUP BY tss.test_suite_id
    )
    SELECT
      ts.id AS test_suite_id,
      r.pattern AS regex,
      pg.projects_gc,
      ss.pos_gc,
      ss.neg_gc
    FROM test_suite AS ts
    JOIN regex_entity    AS r  ON r.id = ts.regex_id
    JOIN project_groups  AS pg ON pg.regex_id = ts.regex_id
    JOIN suite_strings   AS ss ON ss.test_suite_id = ts.id
    ORDER BY ts.id;
    """
    cur = conn.execute(sql)
    for test_suite_id, regex, projects_gc, pos_gc, neg_gc in cur:
        # Reconstruct projects list
        projects_list = []
        if projects_gc:
            for item in projects_gc.split(SEP):
                if not item:
                    continue
                parts = item.split(KV_SEP, 2)  # id, name, repo
                pid_str = parts[0] if len(parts) > 0 else ""
                name = parts[1] if len(parts) > 1 else ""
                repo = parts[2] if len(parts) > 2 else ""
                try:
                    pid = int(pid_str)
                except ValueError:
                    pid = pid_str
                projects_list.append({"id": pid, "name": name, "repo": repo})

        def parse_strings(gc: str) -> list:
            if not gc:
                return []
            out = []
            for item in gc.split(SEP):
                if not item:
                    continue
                fields = item.split(STR_FSEP)
                # Expect 7 fields; pad if necessary
                fields += [""] * (7 - len(fields))
                sid, subject, func, full_s, partial_s, start_s, end_s = fields[:7]
                try:
                    sid = int(sid)
                except ValueError:
                    pass
                def to_int(x, default=None):
                    try:
                        return int(x)
                    except (TypeError, ValueError):
                        return default
                out.append({
                    "id": sid,
                    "subject": subject,
                    "func": func,
                    "full_match": to_int(full_s, 0),
                    "partial_match": to_int(partial_s, 0),
                    "first_sub_match_start": to_int(start_s, -1),
                    "first_sub_match_end": to_int(end_s, -1),
                })
            return out

        pos = parse_strings(pos_gc)
        neg = parse_strings(neg_gc)

        yield {
            "test_suite_id": test_suite_id,
            "regex": regex,
            "projects": projects_list,
            "positive_strings": pos,
            "negative_strings": neg,
        }


def stream_ndjson(rows: Iterable[Dict[str, Any]], out_path: str) -> None:
    with open(out_path, "w", encoding="utf-8") as fh:
        dump = lambda obj: json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
        for obj in rows:
            fh.write(dump(obj) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True, help="Path to the SQLite database file")
    ap.add_argument("--output", required=True, help="Path to the output NDJSON file")
    args = ap.parse_args()

    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)  # read-only
    try:
        conn.execute("PRAGMA query_only = ON;")
        conn.row_factory = None  # tuples

        rows_iter = iter_rows_json1(conn) if has_json1(conn) else iter_rows_concat(conn)
        stream_ndjson(rows_iter, args.output)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
