
SELECT
    test_suite.id AS test_suite_id,
    test_suite.regex_id AS truth_regex_id,
    truth_regex.pattern AS truth_regex,
    test_suite_result.regex_id AS candidate_regex_id,
    candidate_regex.pattern AS candidate_regex
FROM test_suite
INNER JOIN test_suite_result ON test_suite.id = test_suite_result.test_suite_id
INNER JOIN regex_entity AS truth_regex ON truth_regex.id = test_suite.regex_id
INNER JOIN regex_entity AS candidate_regex ON candidate_regex.id = test_suite_result.regex_id
-- add this order by to get better cache performance.
ORDER BY
    truth_regex_id,
    candidate_regex_id;