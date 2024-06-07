package edu.purdue.dualitylab.evaluation.model;

import dk.brics.automaton.AutomatonCoverage;

import java.util.Set;

public record RegexTestSuite(
        long projectId,
        long regexId,
        String pattern,
        Set<RegexTestSuiteString> strings,
        AutomatonCoverage.VisitationInfoSummary fullMatchCoverage,
        AutomatonCoverage.VisitationInfoSummary partialMatchCoverage
) {
}
