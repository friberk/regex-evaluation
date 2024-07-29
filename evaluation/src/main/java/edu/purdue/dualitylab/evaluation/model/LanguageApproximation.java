package edu.purdue.dualitylab.evaluation.model;

import dk.brics.automaton.Automaton;
import dk.brics.automaton.GenerateStrings;
import edu.purdue.dualitylab.evaluation.safematch.SafeMatcher;

import java.time.Duration;
import java.util.Set;
import java.util.concurrent.ExecutorService;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

public record LanguageApproximation(
        Set<StringWithSubMatch> positive,
        Set<String> negative
) {
    public static LanguageApproximation create(Automaton regexAutomaton, SafeMatcher safeMatcher) throws IllegalArgumentException {
        Set<StringWithSubMatch> positive = GenerateStrings.generateStrings(regexAutomaton, 3, true).stream()
                .flatMap(positiveString -> StringWithSubMatch.create(positiveString, safeMatcher).stream())
                .collect(Collectors.toSet());
        Set<String> negative = GenerateStrings.generateStrings(regexAutomaton, 3, false);
        return new LanguageApproximation(positive, negative);
    }

    public double eSimilarity(Pattern otherRegex, SafeMatcher.MatchMode matchMode, ExecutorService safeMatchExecutionContext) {
        SafeMatcher otherRegexSafeMatcher = new SafeMatcher(otherRegex, safeMatchExecutionContext);
        int numPositive = 0;
        int numNegative = 0;
        for (StringWithSubMatch positiveString : positive) {
            SafeMatcher.MatchResult matchResult = otherRegexSafeMatcher.match(positiveString, matchMode, Duration.ofSeconds(15));
            if (matchResult.matches()) {
                numPositive++;
            }
        }

        for (String negativeString : negative) {
            SafeMatcher.MatchResult matchResult = otherRegexSafeMatcher.match(negativeString, matchMode, Duration.ofSeconds(15));
            if (matchResult.mismatches()) {
                numNegative++;
            }
        }

        return GenerateStrings.eSimilarity(numPositive, numNegative, positive().size(), negative().size());
    }
}
