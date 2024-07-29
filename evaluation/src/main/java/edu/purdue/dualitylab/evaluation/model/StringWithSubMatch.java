package edu.purdue.dualitylab.evaluation.model;

import edu.purdue.dualitylab.evaluation.safematch.SafeMatcher;

import java.time.Duration;
import java.util.Optional;

public record StringWithSubMatch(
        String wholeString,
        int subMatchStart,
        int subMatchEnd
) {
    public static Optional<StringWithSubMatch> create(String positiveString, SafeMatcher matcher) {
        Optional<SafeMatcher.PartialMatchResult> matchResult = matcher.partialMatch(positiveString, Duration.ofSeconds(15));
        return matchResult.map(result -> new StringWithSubMatch(positiveString, result.start(), result.end()));
    }
}
