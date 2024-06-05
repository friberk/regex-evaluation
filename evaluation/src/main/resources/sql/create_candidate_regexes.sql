CREATE TEMPORARY TABLE IF NOT EXISTS candidate_regexes_and_origins AS
    -- records a statically (and dynamically) extracted regex, the source originating-project, and the specific source usage
SELECT regex_entity.id AS regex_id, project_spec.id AS project_id, regex_source_usage.id AS source_usage_id
FROM regex_source_usage
    -- take regexes that are static and dynamic and have source usages
INNER JOIN regex_entity ON regex_source_usage.regex_id = regex_entity.id
    -- also pull project info
INNER JOIN project_spec ON regex_source_usage.project_id = project_spec.id
WHERE
    regex_entity.static = TRUE AND
    regex_entity.dynamic = TRUE AND
    IS_METACHAR_REGEX(regex_entity.pattern) IS TRUE;