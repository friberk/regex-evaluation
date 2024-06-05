
INSERT INTO test_suite (project_id, regex_id, node_coverage, edge_coverage, edge_pair_coverage)
VALUES
    (?1, ?2, ?3, ?4, ?5)
ON CONFLICT DO NOTHING;
