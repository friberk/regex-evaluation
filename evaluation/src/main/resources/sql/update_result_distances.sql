
UPDATE test_suite_result
SET ast_distance = ?1,
    automaton_distance = ?2
WHERE
    test_suite_id = ?3 AND regex_id = ?4;