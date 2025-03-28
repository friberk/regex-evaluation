
CREATE TABLE IF NOT EXISTS internet_regex (
    -- the id for this internet regex
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    -- id of the internet regex source: 1 for SO,
    origin_id INT NOT NULL,
    -- the regex's pattern
    pattern TEXT NOT NULL,
    -- where this regex came from
    origin_uri TEXT,
    -- patterns are unique
    UNIQUE (pattern)
);

CREATE TABLE IF NOT EXISTS test_suite_internet_result (
    -- foreign key to test suites solutions database
    test_suite_id INTEGER NOT NULL,
    -- the internet regex that is a solution
    internet_regex_id INTEGER NOT NULL,
    -- if true, then this result is a "full match" test suite result. NULL indicates that we couldn't assess if it
    -- matches or not because the test suite did not satisfy the filter
    full_match_result BOOLEAN,
    -- if true, then this result is a "partial match" test suite result. NULL indicates that we couldn't assess if it
    -- matches or not because the test suite did not satisfy the filter
    partial_match_result BOOLEAN,
    -- relative coverage values
    full_node_coverage REAL DEFAULT NULL,
    full_edge_coverage REAL DEFAULT NULL,
    full_edge_pair_coverage REAL DEFAULT NULL,
    partial_node_coverage REAL DEFAULT NULL,
    partial_edge_coverage REAL DEFAULT NULL,
    partial_edge_pair_coverage REAL DEFAULT NULL,
    ast_distance INTEGER DEFAULT -1,
    auto_distance REAL DEFAULT NULL,
    -- foreign key to internet regex
    FOREIGN KEY (internet_regex_id) REFERENCES internet_regex(id)
);
