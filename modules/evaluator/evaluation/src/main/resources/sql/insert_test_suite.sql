
INSERT INTO test_suite (
                        project_id,
                        regex_id,
                        full_node_coverage,
                        full_edge_coverage,
                        full_edge_pair_coverage,
                        partial_node_coverage,
                        partial_edge_coverage,
                        partial_edge_pair_coverage)
VALUES
    (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)
ON CONFLICT DO NOTHING;
