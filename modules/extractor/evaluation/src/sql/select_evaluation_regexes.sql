
SELECT regex_entity.id, regex_entity.pattern, regex_source_usage.project_id, regex_source_usage.id FROM regex_source_usage
    -- join source usages with regexes
INNER JOIN regex_entity ON regex_source_usage.regex_id = regex_entity.id
    -- only select source usages that didn't originate from the project the test suite came from
WHERE regex_source_usage.project_id != :project_id;
