package edu.institution.lab.evaluation.model;

import dk.brics.automaton.AutomatonCoverage;
import edu.institution.lab.evaluation.db.DbField;

public record RawTestSuiteRow(
        @DbField(name = "test_suite_id") Long testSuiteId,
        @DbField(name = "project_id") Long projectId,
        @DbField(name = "regex_id") Long regexId,
        @DbField(name = "pattern") String pattern,
        @DbField(name = "full_node_coverage") Double fullNodeCoverage,
        @DbField(name = "full_edge_coverage") Double fullEdgeCoverage,
        @DbField(name = "full_edge_pair_coverage") Double fullEdgePairCoverage,
        @DbField(name = "partial_node_coverage") Double partialNodeCoverage,
        @DbField(name = "partial_edge_coverage") Double partialEdgeCoverage,
        @DbField(name = "partial_edge_pair_coverage") Double partialEdgePairCoverage,
        @DbField(name = "string_id") Long stringId,
        @DbField(name = "subject") String subject,
        @DbField(name = "func") String func,
        @DbField(name = "full_match") Boolean fullMatch,
        @DbField(name = "partial_match") Boolean partialMatch,
        @DbField(name = "first_sub_match_start") Integer partialMatchStartIdx,
        @DbField(name = "first_sub_match_end") Integer partialMatchEndIdx
) {
    private MatchStatus matchStatus() {
        return new MatchStatus(fullMatch, partialMatch, partialMatchStartIdx, partialMatchEndIdx);
    }

    public AutomatonCoverage.VisitationInfoSummary fullCoverageSummary() {
        return new AutomatonCoverage.VisitationInfoSummary(fullNodeCoverage, fullEdgeCoverage, fullEdgePairCoverage);
    }

    public AutomatonCoverage.VisitationInfoSummary partialCoverageSummary() {
        return new AutomatonCoverage.VisitationInfoSummary(partialNodeCoverage, partialEdgeCoverage, partialEdgePairCoverage);
    }

    public RegexTestSuiteString testSuiteString() {
        return new RegexTestSuiteString(stringId(), subject(), projectId(), func(), matchStatus());
    }
}
