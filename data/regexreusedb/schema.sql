-- regex_entity definition

CREATE TABLE regex_entity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    -- the actual regex pattern
    pattern TEXT NOT NULL,
    -- any flags associated with this pattern
    flags TEXT,
    -- determines if the regex was found statically
    static BOOLEAN DEFAULT FALSE,
    -- determines if this regex was found dynamically. Set this flag when inserting a subject and there was no
    -- corresponding statically extracted regex. False means it was statically extracted, true means it was dynamically
    -- extracted and there was no static regex with the same pattern
    dynamic BOOLEAN DEFAULT FALSE,
    -- all regexes should be a unique pattern-flags combination
    UNIQUE (pattern, flags)
);

CREATE INDEX regex_entity_by_pattern ON regex_entity(pattern);
CREATE INDEX idx_regex_entity_id ON regex_entity(id);

-- project_spec definition

CREATE TABLE project_spec (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    -- the project name
    name TEXT NOT NULL,
    -- the github repo URL for this project
    repo TEXT NOT NULL,
    -- a license associated with this project, if any
    license TEXT,
    -- the source language for this project
    language TEXT,
    -- the start count for this project
    downloads INTEGER DEFAULT 0,
    -- ensure that projects are unique by name and repository
    UNIQUE (name, repo)
);

CREATE INDEX project_spec_by_repo ON project_spec(repo);

-- regex_source_usage definition

CREATE TABLE regex_source_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    -- where in the source file this usage occurred
    line_no INTEGER NOT NULL,
    -- which file this usage occurred in, relative to the project root
    source_file TEXT NOT NULL,
    -- the commit of the project at the origin
    commit_hash TEXT,
    -- foreign key reference to the project that this usage occurred in
    project_id INTEGER,
    -- the regex found at this location
    regex_id INTEGER,
    FOREIGN KEY (project_id) REFERENCES project_spec(id),
    FOREIGN KEY (regex_id) REFERENCES regex_entity(id),
    -- each usage should be unique
    UNIQUE (line_no, source_file, commit_hash, project_id, regex_id)
);

-- test_suite definition

CREATE TABLE test_suite (
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

CREATE INDEX IF NOT EXISTS idx_test_suite_regex_id ON test_suite(regex_id);

-- test_suite_string definition

CREATE TABLE test_suite_string (
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

-- test_suite_result definition

CREATE TABLE test_suite_result (
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
    -- the distance between this candidate and the truth automaton under full-matching context
    full_automaton_distance DOUBLE,
    -- the distance between this candidate and the truth automaton under partial-matching context
    partial_automaton_distance DOUBLE,
    -- relative coverage values. Default to null and update them later
    full_node_coverage DOUBLE DEFAULT NULL,
    full_edge_coverage DOUBLE DEFAULT NULL,
    full_edge_pair_coverage DOUBLE DEFAULT NULL,
    partial_node_coverage DOUBLE DEFAULT NULL,
    partial_edge_coverage DOUBLE DEFAULT NULL,
    partial_edge_pair_coverage DOUBLE DEFAULT NULL,

    -- this table's primary key is a composite. Every test suite/regex pair should be unique
    PRIMARY KEY (test_suite_id, regex_id),
    FOREIGN KEY (test_suite_id) REFERENCES test_suite(id),
    FOREIGN KEY (regex_id) REFERENCES regex_entity(id),
    FOREIGN KEY (project_id) REFERENCES project_spec(id)
);

CREATE INDEX IF NOT EXISTS idx_test_suite_result_regex_id ON test_suite_result(regex_id);

CREATE INDEX IF NOT EXISTS idx_test_suite_result_project_id ON test_suite_result(project_id);
