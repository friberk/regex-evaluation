
CREATE TABLE internet_regex (
    -- the id for this internet regex
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    -- the regex's pattern
    pattern TEXT NOT NULL,
    -- where this regex came from
    origin_uri TEXT,
    -- id of the internet regex source
    origin_id INT NOT NULL
);

CREATE TABLE internet_test_suite_result (
    -- if true, then this result is a "full match" test suite result. NULL indicates that we couldn't assess if it
    -- matches or not because the test suite did not satisfy the filter
    full_match_result BOOLEAN,
    -- if true, then this result is a "partial match" test suite result. NULL indicates that we couldn't assess if it
    -- matches or not because the test suite did not satisfy the filter
    partial_match_result BOOLEAN
);
