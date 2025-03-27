
-- merge databases together
BEGIN TRANSACTION;

-- First, copy over unique projects
INSERT OR IGNORE INTO project_spec (name, repo, license, language, downloads)
SELECT name, repo, license, language, downloads FROM merge_db.project_spec;

-- Copy over regex entities
INSERT INTO regex_entity (pattern, flags, static, dynamic)
SELECT pattern, flags, static, dynamic
FROM merge_db.regex_entity
WHERE TRUE
ON CONFLICT DO
    UPDATE SET static = (excluded.static | regex_entity.static), dynamic = (excluded.dynamic | regex_entity.dynamic);

-- Update foreign keys on incoming entities
CREATE TEMPORARY TABLE incoming_regex_source_usage AS
SELECT * FROM merge_db.regex_source_usage;

CREATE TEMPORARY TABLE incoming_regex_subjects AS
SELECT * FROM merge_db.regex_subject;

CREATE TEMPORARY TABLE incoming_project_processing_report AS
SELECT * FROM merge_db.project_processing_report;

UPDATE incoming_regex_source_usage
SET regex_id=(
    SELECT id FROM regex_entity
    WHERE pattern=
              -- lookup the pattern we're curious about
          (
              SELECT pattern FROM merge_db.regex_entity
              WHERE id=incoming_regex_source_usage.regex_id
          )
);

UPDATE incoming_regex_source_usage
SET project_id=(
    SELECT id FROM project_spec
    WHERE repo=
              -- lookup the pattern we're curious about
          (
              SELECT repo FROM merge_db.project_spec
              WHERE id=incoming_regex_source_usage.project_id
          )
);

UPDATE incoming_regex_subjects
SET regex_id=(
    SELECT id FROM regex_entity
    WHERE pattern=
              -- lookup the pattern we're curious about
          (
              SELECT pattern FROM merge_db.regex_entity
              WHERE id=incoming_regex_subjects.regex_id
          )
);

UPDATE incoming_regex_subjects
SET project_id=(
    SELECT id FROM project_spec
    WHERE repo=
              -- lookup the pattern we're curious about
          (
              SELECT repo FROM merge_db.project_spec
              WHERE id=incoming_regex_subjects.project_id
          )
);

UPDATE incoming_project_processing_report
SET project_id=(
    SELECT id FROM project_spec
    WHERE repo=
              -- lookup the pattern we're curious about
          (
              SELECT repo FROM merge_db.project_spec
              WHERE id=incoming_project_processing_report.project_id
          )
);

-- now that foreign keys are resolved, copy everything
INSERT OR IGNORE INTO regex_source_usage (line_no, source_file, commit_hash, project_id, regex_id)
SELECT line_no, source_file, commit_hash, project_id, regex_id FROM incoming_regex_source_usage;

INSERT OR IGNORE INTO regex_subject (regex_id, project_id, subject, matches, func)
SELECT regex_id, project_id, subject, matches, func FROM incoming_regex_subjects;

INSERT OR IGNORE INTO project_processing_report (project_id, status)
SELECT project_id, status FROM incoming_project_processing_report;

COMMIT;