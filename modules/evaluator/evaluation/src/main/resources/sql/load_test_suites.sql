
-- pull the regex pattern, originating project, source usage, example string, and regex function
SELECT
    regex_entity.id AS regex_id,
    regex_entity.pattern,
    candidate_regexes_and_origins.project_id,
    source_usage_id,
    regex_subject.project_id AS subject_project_id,
    subject,
    func
FROM regex_subject
    -- pull from the above table, joining on project and regex id
INNER JOIN candidate_regexes_and_origins ON candidate_regexes_and_origins.project_id = regex_subject.project_id AND candidate_regexes_and_origins.regex_id = regex_subject.regex_id
    -- pull the regex entity to get the pattern
INNER JOIN regex_entity ON candidate_regexes_and_origins.regex_id = regex_entity.id
WHERE
    FILTER_REGEX_PATTERN(regex_entity.pattern, 5) AND
    LENGTH(regex_subject.subject) <= ?1
    -- group by regex id
ORDER BY regex_entity.id;