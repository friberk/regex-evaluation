SELECT
    test_suite.id AS test_suite_id,
    project_id,
    regex_id,
    regex_entity.pattern,
    full_node_coverage,
    full_edge_coverage,
    full_edge_pair_coverage,
    partial_node_coverage,
    partial_edge_coverage,
    partial_edge_pair_coverage,
    test_suite_string.id AS string_id,
    subject,
    func,
    full_match,
    partial_match,
    test_suite_string.first_sub_match_start,
    test_suite_string.first_sub_match_end
FROM test_suite
INNER JOIN test_suite_string ON test_suite.id = test_suite_string.test_suite_id
INNER JOIN regex_entity ON test_suite.regex_id = regex_entity.id
ORDER BY test_suite.id;