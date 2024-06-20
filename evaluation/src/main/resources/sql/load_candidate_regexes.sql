
WITH regex_not_in_test_suite_project AS (
    SELECT regex_id, project_id
    FROM regex_source_usage
    -- find all source usages that don't come from the test suite's project
    WHERE project_id != ?1
    GROUP BY regex_id
)
SELECT id, regex_not_in_test_suite_project.project_id, regex_entity.pattern
FROM regex_entity
INNER JOIN regex_not_in_test_suite_project ON regex_not_in_test_suite_project.regex_id = regex_entity.id
WHERE
    FILTER_REGEX_PATTERN(regex_entity.pattern, 5) AND
    static = TRUE
;