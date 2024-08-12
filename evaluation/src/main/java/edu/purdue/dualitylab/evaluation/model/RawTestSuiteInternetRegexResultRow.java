package edu.purdue.dualitylab.evaluation.model;

import edu.purdue.dualitylab.evaluation.db.DbField;

public record RawTestSuiteInternetRegexResultRow(
        @DbField(name = "test_suite_id") Long testSuiteId,
        @DbField(name = "internet_regex_id") Long internetRegexId,
        @DbField(name = "internet_regex_pattern") String internetRegexPattern
) {
}
