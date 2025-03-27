package edu.institution.lab.evaluation.model;

import dk.brics.automaton.AutomatonCoverage;
import edu.institution.lab.evaluation.safematch.SafeMatcher;

import java.util.Set;
import java.util.function.Predicate;
import java.util.stream.Stream;

public record RegexTestSuite(
        Long id,
        long projectId,
        long regexId,
        String pattern,
        Set<RegexTestSuiteString> strings,
        AutomatonCoverage.VisitationInfoSummary fullMatchCoverage,
        AutomatonCoverage.VisitationInfoSummary partialMatchCoverage
) {
    /**
     * Determines if this test suite has at least one positive string and at least one negative string
     * @param matchMode What kind of matches there should be, either full or partial
     * @param minCount How many strings of each type are necessary
     * @return True if this test suite is valid
     */
    public boolean hasPositiveAndNegativeStrings(SafeMatcher.MatchMode matchMode, long minCount) {

        Predicate<MatchStatus> isPositiveString =
                (MatchStatus matchStatus) -> matchMode == SafeMatcher.MatchMode.FULL ? matchStatus.fullMatch() : matchStatus.partialMatch();

        Stream<MatchStatus> positiveStrings = strings.stream()
                .map(RegexTestSuiteString::matchStatus)
                .filter(isPositiveString);

        boolean hasPositiveString = minCount > 1 ? positiveStrings.count() >= minCount : positiveStrings.anyMatch(isPositiveString);

        Stream<MatchStatus> negativeStrings = strings.stream()
                .map(RegexTestSuiteString::matchStatus)
                .filter(isPositiveString.negate());

        boolean hasNegativeString = minCount > 1 ? negativeStrings.count() >= minCount : negativeStrings.anyMatch(isPositiveString.negate());

        return hasPositiveString && hasNegativeString;
    }
}
