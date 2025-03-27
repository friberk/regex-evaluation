package edu.institution.lab.evaluation.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonAlias;
import java.util.List;
import java.util.Optional;

public record ManualTestSuite(
        @JsonProperty("regex_pattern")
        @JsonAlias("regexPattern")
        Optional<String> regexPattern,

        @JsonProperty("regex_id")
        @JsonAlias("regexId")
        long regexId,

        @JsonProperty("test_suite_id")
        @JsonAlias("testSuiteId")
        long testSuiteId,

        @JsonProperty("project_id")
        @JsonAlias("projectId")
        long projectId,

        @JsonProperty("strings")
        List<TestString> strings,

        @JsonProperty("test_string_count")
        @JsonAlias("testStringCount")
        int testStringCount
) {
}
