package edu.institution.lab.evaluation.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonAlias;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import dk.brics.automaton.AutomatonCoverage;

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public record ManualTestSuiteResult(
        @JsonProperty("regex_id")
        @JsonAlias({"id", "regexId"})
        long id,
        @JsonProperty("project_id")
        @JsonAlias("projectId")
        long projectId,
        @JsonProperty("regex_pattern")
        @JsonAlias({"regexPattern", "pattern"})
        String pattern,
        @JsonProperty("full_coverage_summary")
        @JsonAlias("fullCoverageSummary")
        AutomatonCoverage.VisitationInfoSummary fullCoverageSummary
) {
}
