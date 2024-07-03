
INSERT INTO test_suite_String (test_suite_id, subject, func, full_match, partial_match, first_sub_match_start, first_sub_match_end)
VALUES
    (?1, ?2, ?3, ?4, ?5, ?6, ?7)
ON CONFLICT DO NOTHING;
