ALTER TABLE test_suite_result ADD COLUMN ast_distance INTEGER DEFAULT -1;
ALTER TABLE test_suite_result ADD COLUMN full_automaton_distance DOUBLE;
ALTER TABLE test_suite_result ADD COLUMN partial_automaton_distance DOUBLE;