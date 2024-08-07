
UPDATE test_suite
SET full_node_coverage = ?1,
    full_edge_coverage = ?2,
    full_edge_pair_coverage = ?3,
    partial_node_coverage = ?4,
    partial_edge_coverage = ?5,
    partial_edge_pair_coverage = ?6
WHERE
    id = ?7;