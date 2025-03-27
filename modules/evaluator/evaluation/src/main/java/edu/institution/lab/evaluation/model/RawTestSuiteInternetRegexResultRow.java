package edu.institution.lab.evaluation.model;

import edu.institution.lab.evaluation.db.DbField;

public record RawTestSuiteInternetRegexResultRow(
        @DbField(name = "test_suite_id") Long testSuiteId,
        @DbField(name = "internet_regex_id") Long internetRegexId,
        @DbField(name = "internet_regex_pattern") String internetRegexPattern
) {
}
