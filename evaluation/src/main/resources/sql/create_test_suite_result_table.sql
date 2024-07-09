
DROP TABLE IF EXISTS test_suite_result;

CREATE TABLE IF NOT EXISTS test_suite_result (
    -- the test suite that this result belongs to
    test_suite_id INTEGER NOT NULL,
    -- the regex that satisfies this test suite
    regex_id INTEGER NOT NULL,
    -- the project that this regex solution came from
    project_id INTEGER NOT NULL,
    -- if true, then this result is a "full match" test suite result. NULL indicates that we couldn't assess if it
    -- matches or not because the test suite did not satisfy the filter
    full_match_result BOOLEAN,
    -- if true, then this result is a "partial match" test suite result. NULL indicates that we couldn't assess if it
    -- matches or not because the test suite did not satisfy the filter
    partial_match_result BOOLEAN,
    -- the distance between this candidate and the truth AST
    ast_distance INTEGER,
    -- the distance between this candidate and the truth automaton
    automaton_distance DOUBLE,
    -- this table's primary key is a composite. Every test suite/regex pair should be unique
    PRIMARY KEY (test_suite_id, regex_id),
    FOREIGN KEY (test_suite_id) REFERENCES test_suite(id),
    FOREIGN KEY (regex_id) REFERENCES regex_entity(id),
    FOREIGN KEY (project_id) REFERENCES project_spec(id)
);
