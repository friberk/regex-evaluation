
-- ignore duplicate patterns
INSERT OR IGNORE INTO internet_regex (origin_id, pattern, origin_uri)
VALUES (?1, ?2, ?3);