
BEGIN;

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

---------------------------------------------------------------------------
-- next create a mapping of old regex entity ids to new regex entity ids --
---------------------------------------------------------------------------
-- create staging table
CREATE TEMPORARY TABLE merge_db_regex_entity AS
SELECT * FROM merge_db.regex_entity;

-- index on pattern to make join easier
CREATE INDEX merge_db_regex_entity_by_pattern ON merge_db_regex_entity(pattern);
CREATE INDEX IF NOT EXISTS regex_entity_by_pattern ON regex_entity(pattern);

-- create a mapping table
CREATE TEMPORARY TABLE regex_id_mappings AS
SELECT merge_db_regex_entity.id AS old_regex_id, regex_entity.id AS new_regex_id
FROM merge_db_regex_entity
INNER JOIN regex_entity ON regex_entity.pattern = merge_db_regex_entity.pattern;

-- index mapping by old regex_id because that's what we're going to be looking up by
CREATE INDEX regex_id_mappings_by_old_regex_id ON regex_id_mappings(old_regex_id);

-------------------------------------------------------
-- Do approximately the same thing for project_specs --
-------------------------------------------------------
-- create a temporary table of incoming data
CREATE TEMPORARY TABLE merge_db_project_spec AS
SELECT * FROM merge_db.project_spec;

-- index on pattern to make join easier
CREATE INDEX merge_db_project_spec_by_repo ON merge_db_project_spec(repo);
CREATE INDEX IF NOT EXISTS project_spec_by_repo ON project_spec(repo);

-- create a mapping table
CREATE TEMPORARY TABLE project_id_mapping AS
SELECT merge_db_project_spec.id AS old_project_id, project_spec.id AS new_project_id
FROM merge_db_project_spec
INNER JOIN project_spec ON project_spec.repo = merge_db_project_spec.repo;

-- index the mapping table by the old id
CREATE INDEX project_id_mapping_by_old_id ON project_id_mapping(old_project_id);

---------------------------------------------------------------------------
-- Now that we have lookup tables, we can actually merge everything over --
---------------------------------------------------------------------------

-- update incoming regex source usages --
CREATE TEMPORARY TABLE incoming_regex_source_usage AS SELECT * FROM merge_db.regex_source_usage;
UPDATE incoming_regex_source_usage
SET regex_id = regex_mapping.new_regex_id, project_id = project_mapping.new_project_id
FROM
    project_id_mapping AS project_mapping,
    regex_id_mappings AS regex_mapping
WHERE
    incoming_regex_source_usage.regex_id = regex_mapping.old_regex_id AND
    incoming_regex_source_usage.project_id = project_mapping.old_project_id;

INSERT OR IGNORE INTO regex_source_usage (line_no, source_file, commit_hash, project_id, regex_id)
SELECT line_no, source_file, commit_hash, project_id, regex_id FROM incoming_regex_source_usage;

-- update incoming regex subjects
CREATE TEMPORARY TABLE incoming_regex_subject AS SELECT * FROM merge_db.regex_subject;
UPDATE incoming_regex_subject
SET regex_id = regex_mapping.new_regex_id, project_id = project_mapping.new_project_id
FROM
    project_id_mapping AS project_mapping,
    regex_id_mappings AS regex_mapping
WHERE
    incoming_regex_subject.regex_id = regex_mapping.old_regex_id AND
    incoming_regex_subject.project_id = project_mapping.old_project_id;

INSERT OR IGNORE INTO regex_subject (regex_id, project_id, subject, matches, func)
SELECT regex_id, project_id, subject, matches, func FROM incoming_regex_subject;

-- update package processing reports
CREATE TEMPORARY TABLE incoming_project_processing_report AS SELECT * FROM merge_db.project_processing_report;
UPDATE incoming_project_processing_report
SET project_id = project_mapping.new_project_id
FROM
    project_id_mapping AS project_mapping
WHERE
    incoming_project_processing_report.project_id = project_mapping.old_project_id;
INSERT OR IGNORE INTO project_processing_report (project_id, status)
SELECT project_id, status FROM incoming_project_processing_report;

COMMIT;