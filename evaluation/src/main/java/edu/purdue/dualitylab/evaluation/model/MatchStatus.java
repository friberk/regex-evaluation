package edu.purdue.dualitylab.evaluation.model;

import edu.purdue.dualitylab.evaluation.safematch.SafeMatcher;

import java.time.Duration;
import java.util.Optional;
import java.util.regex.Matcher;

public record MatchStatus(
        boolean fullMatch,
        boolean partialMatch
) {
    public static MatchStatus compute(Matcher matcher) {
        boolean fullMatch = matcher.matches();
        matcher.reset();
        boolean partialMatch = matcher.find();
        return new MatchStatus(fullMatch, partialMatch);
    }

    public static Optional<MatchStatus> compute(SafeMatcher safeMatcher, CharSequence string) {
        SafeMatcher.MatchResult result = safeMatcher.match(string, SafeMatcher.MatchMode.FULL, Duration.ofSeconds(30));
        if (result == SafeMatcher.MatchResult.TIMEOUT) {
            // if we get a timeout, bail
            return Optional.empty();
        }

        boolean fullMatch = result == SafeMatcher.MatchResult.MATCH;

        result = safeMatcher.match(string, SafeMatcher.MatchMode.PARTIAL, Duration.ofSeconds(30));
        if (result == SafeMatcher.MatchResult.TIMEOUT) {
            // if we get a timeout, bail
            return Optional.empty();
        }

        boolean partialMatch = result == SafeMatcher.MatchResult.MATCH;

        return Optional.of(new MatchStatus(fullMatch, partialMatch));
    }
}
