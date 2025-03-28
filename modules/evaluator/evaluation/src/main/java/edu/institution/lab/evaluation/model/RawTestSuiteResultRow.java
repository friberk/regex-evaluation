package edu.institution.lab.evaluation.model;

import edu.institution.lab.evaluation.db.DbField;
import edu.institution.lab.evaluation.util.Pair;

public record RawTestSuiteResultRow(
    @DbField(name = "test_suite_id") Long testSuiteId,
    @DbField(name = "truth_regex_id") Long truthRegexId,
    @DbField(name = "truth_regex") String truthRegex,
    @DbField(name = "candidate_regex_id") Long candidateRegexId,
    @DbField(name = "candidate_regex") String candidateRegex
) {

    public Pair<Long, Long> testSuiteInfoKey() {
        return Pair.of(testSuiteId, truthRegexId);
    }

    public Pair<Long, Long> resultPrimaryKey() {
        return new Pair<>(testSuiteId, candidateRegexId);
    }
}
