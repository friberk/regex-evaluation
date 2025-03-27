
DROP TABLE IF EXISTS candidate_regexes_and_origins;
CREATE TEMPORARY TABLE candidate_regexes_and_origins AS
    -- records a statically (and dynamically) extracted regex, the source originating-project, and the specific source usage
SELECT regex_entity.id as regex_id, project_spec.id as project_id, regex_source_usage.id as source_usage_id FROM regex_source_usage
    -- take regexes that are static and dynamic and have source usages
INNER JOIN regex_entity ON regex_source_usage.regex_id = regex_entity.id AND regex_entity.static IS TRUE AND regex_entity.dynamic IS TRUE
    -- also pull project info
INNER JOIN project_spec ON regex_source_usage.project_id = project_spec.id;

--!

-- pull the regex pattern, originating project, source usage, example string, and regex function
SELECT regex_entity.id as regex_id, regex_entity.pattern, candidate_regexes_and_origins.project_id, source_usage_id, subject, func FROM regex_subject
    -- pull from the above table, joining on project and regex id
INNER JOIN candidate_regexes_and_origins ON candidate_regexes_and_origins.project_id = regex_subject.project_id AND candidate_regexes_and_origins.regex_id = regex_subject.regex_id
    -- pull the regex entity to get the pattern
INNER JOIN regex_entity ON candidate_regexes_and_origins.regex_id = regex_entity.id
    -- group by regex id
ORDER BY regex_entity.id;
