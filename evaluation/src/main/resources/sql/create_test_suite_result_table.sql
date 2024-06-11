
DROP TABLE IF EXISTS test_suite_result;

CREATE TABLE IF NOT EXISTS test_suite_result (
    -- the test suite that this result belongs to
    test_suite_id INTEGER NOT NULL,
    -- the regex that satisfies this test suite
    regex_id INTEGER NOT NULL,
    -- this table's primary key is a composite. Every test suite/regex pair should be unique
    PRIMARY KEY (test_suite_id, regex_id),
    FOREIGN KEY (test_suite_id) REFERENCES test_suite(id),
    FOREIGN KEY (regex_id) REFERENCES regex_entity(id)
);
