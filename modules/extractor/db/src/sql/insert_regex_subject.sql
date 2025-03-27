
WITH
    matching_regex AS (
        SELECT id FROM regex_entity WHERE pattern=:pattern
    )
INSERT OR IGNORE INTO regex_subject (project_id, subject, matches, func, regex_id)
SELECT
    :project_id,
    :subject,
    :matches,
    :func,
    id FROM matching_regex
       ;