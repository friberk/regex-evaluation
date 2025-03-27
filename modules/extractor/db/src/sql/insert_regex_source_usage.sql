
-- insert regex source usage
WITH
    matching_regex AS (
        SELECT id FROM regex_entity WHERE pattern=:pattern
    )
INSERT OR IGNORE INTO regex_source_usage (line_no, source_file, commit_hash, project_id, regex_id)
SELECT
        :line_no,
        :source_file,
        :commit_hash,
        :project_id,
        id FROM matching_regex
       ;
