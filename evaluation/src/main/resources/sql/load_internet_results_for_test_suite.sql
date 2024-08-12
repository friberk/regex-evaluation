
SELECT
    test_suite_id,
    internet_regex_id,
    internet_regex.pattern AS internet_regex_pattern
FROM test_suite_internet_result
INNER JOIN internet_regex ON internet_regex.id = test_suite_internet_result.internet_regex_id
WHERE
    test_suite_id = ?1;