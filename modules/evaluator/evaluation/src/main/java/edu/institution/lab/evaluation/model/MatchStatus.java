package edu.institution.lab.evaluation.model;

import edu.institution.lab.evaluation.safematch.SafeMatcher;

import java.time.Duration;
import java.util.Optional;

public record MatchStatus(
        boolean fullMatch,
        boolean partialMatch,
        int partialMatchStartIdx,
        int partialMatchEndIdx
) {
    public static Optional<MatchStatus> compute(SafeMatcher safeMatcher, CharSequence string) {
        SafeMatcher.MatchResult result = safeMatcher.match(string, SafeMatcher.MatchMode.FULL, Duration.ofSeconds(30));
        if (result == SafeMatcher.MatchResult.TIMEOUT) {
            // if we get a timeout, bail
            return Optional.empty();
        }

        boolean fullMatch = result == SafeMatcher.MatchResult.MATCH;

        Optional<SafeMatcher.PartialMatchResult> partialMatchResult = safeMatcher.partialMatch(string, Duration.ofSeconds(30));
        if (partialMatchResult.isEmpty()) {
            // if we get a timeout, bail
            return Optional.empty();
        }

        SafeMatcher.PartialMatchResult partialMatchInfo = partialMatchResult.get();
        boolean partialMatch = partialMatchInfo.matchResult() == SafeMatcher.MatchResult.MATCH;

        return Optional.of(new MatchStatus(fullMatch, partialMatch, partialMatchInfo.start(), partialMatchInfo.end()));
    }
}
