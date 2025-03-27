
CREATE TABLE IF NOT EXISTS dfa_blobs (
    -- id of the regex we are interested in
    regex_id INTEGER PRIMARY KEY,
    dfa BLOB NOT NULL
);


