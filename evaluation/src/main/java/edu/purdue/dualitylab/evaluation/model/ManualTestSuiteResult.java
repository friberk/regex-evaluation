package edu.purdue.dualitylab.evaluation.model;

import dk.brics.automaton.AutomatonCoverage;

public record ManualTestSuiteResult(
        long id,
        long projectId,
        String pattern,
        AutomatonCoverage.VisitationInfoSummary fullCoverageSummary
) {
}
