package edu.purdue.dualitylab.evaluation.model;

import dk.brics.automaton.AutomatonCoverage;

public record RelativeCoverageUpdate(
        long testSuiteId,
        long candidateRegexId,
        AutomatonCoverage.VisitationInfoSummary fullCoverage,
        AutomatonCoverage.VisitationInfoSummary partialCoverage
) {
    public RelativeCoverageUpdate(long testSuiteId,
                                  long candidateRegexId,
                                  AutomatonCoverage coverage) {
        this(testSuiteId, candidateRegexId, coverage.getFullMatchVisitationInfoSummary(), coverage.getPartialMatchVisitationInfoSummary());
    }
}
