package edu.purdue.dualitylab.evaluation.model;

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
}
