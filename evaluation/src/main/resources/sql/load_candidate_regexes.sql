
WITH regex_not_in_test_suite_project AS (
    SELECT regex_id
    FROM regex_source_usage
    -- find all source usages that don't come from the test suite's project
    WHERE project_id != ?1
)
SELECT id, regex_entity.pattern
FROM regex_entity
WHERE
    id IN regex_not_in_test_suite_project AND
    IS_METACHAR_REGEX(regex_entity.pattern) AND
    static = TRUE
;