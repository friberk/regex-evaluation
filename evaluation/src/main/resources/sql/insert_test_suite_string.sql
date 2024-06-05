
INSERT INTO test_suite_String (test_suite_id, subject, func, full_match, partial_match)
VALUES
    (?1, ?2, ?3, ?4, ?5)
ON CONFLICT DO NOTHING;
