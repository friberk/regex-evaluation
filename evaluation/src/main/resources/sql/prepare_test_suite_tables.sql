BEGIN TRANSACTION;

DROP TABLE IF EXISTS test_suite;
CREATE TABLE IF NOT EXISTS test_suite (
    -- test suite id for relationships
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    -- which project this test suite originated from
    project_id INTEGER NOT NULL,
    -- the regex that this test suite belongs to, the ground truth regex
    regex_id INTEGER NOT NULL,
    -- test suite node coverage scores
    full_node_coverage REAL,
    full_edge_coverage REAL,
    full_edge_pair_coverage REAL,
    partial_node_coverage REAL,
    partial_edge_coverage REAL,
    partial_edge_pair_coverage REAL,
    FOREIGN KEY (project_id) REFERENCES project_spec(id),
    FOREIGN KEY (regex_id) REFERENCES regex_entity(id),
    -- each project/regex pair should only have one test suite
    UNIQUE (project_id, regex_id)
);

DROP TABLE IF EXISTS test_suite_string;
CREATE TABLE IF NOT EXISTS test_suite_string (
    -- string id
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    -- which test suite this string belongs to
    test_suite_id INTEGER NOT NULL,
    -- the actual string in question
    subject TEXT NOT NULL,
    -- which function was used to produce this string
    func TEXT,
    -- if this string full matches the subject
    full_match BOOLEAN,
    -- if this string is partially matched by the subject
    partial_match BOOLEAN,
    -- if this string is a partial match, this is the start index of the substring found by the regex. If it is not a
    -- partial match, then it is -1
    first_sub_match_start INTEGER,
    -- if this string is a partial match, this is the end index exclusive of the substring found by the regex. If it
    -- is not a partial match, then it is -1
    first_sub_match_end INTEGER,
    FOREIGN KEY (test_suite_id) REFERENCES test_suite(id),
    -- each test suite should have a unique subject string. Func is factored in so that, if the same string
    -- is run with different functions, we can record that
    UNIQUE (test_suite_id, subject, func)
);

COMMIT;