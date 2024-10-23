package edu.purdue.dualitylab.evaluation.evaluation;

import edu.purdue.dualitylab.evaluation.model.LanguageApproximation;
import edu.purdue.dualitylab.evaluation.model.RegexTestSuite;
import edu.purdue.dualitylab.evaluation.model.RegexTestSuiteSolution;
import edu.purdue.dualitylab.evaluation.model.RegexTestSuiteString;
import edu.purdue.dualitylab.evaluation.safematch.SafeMatcher;
import edu.purdue.dualitylab.evaluation.util.IndeterminateBoolean;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Duration;
import java.util.*;
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutorService;
import java.util.stream.Collectors;

/**
 * Used to find candidates regexes that works for a truth regex.
 */
public class TestSuiteEvaluator implements Callable<Map<Long, Set<RegexTestSuiteSolution>>> {
    private static final Logger logger = LoggerFactory.getLogger(TestSuiteEvaluator.class);

    /**
     * The result of evaluating. Contains the potential candidate and if it's a full/partial match. If one of these
     * operations times out, then it is indeterminate.
     * @param entity The reuse candidate
     * @param fullMatch If this entity full-matches the test suite
     * @param partialMatch If this entity partial-matches the test suite
     */
    private record EvaluationResult(
            CompiledRegexEntity entity,
            IndeterminateBoolean fullMatch,
            IndeterminateBoolean partialMatch
    ) {}

    /**
     * context in which this test suite is evaluated. This evaluation service should be used for performing safe regex
     * matches as well
     */
    private final ExecutorService safeExecutionContext;

    /**
     * The test suite we are actively evaluating
     */
    private final RegexTestSuite testSuite;

    /**
     * Stream of candidate regexes to evaluate
     */
    private final Collection<CompiledRegexEntity> candidates;

    /**
     * How many strings a regex must satisfy to be considered a candidate
     */
    private final double accuracyThreshold;

    /**
     * Language approximation for truth language. Set of positive and negative strings created from the automaton
     */
    private final LanguageApproximation truthLanguageApprox;

    public TestSuiteEvaluator(ExecutorService safeExecutionContext, RegexTestSuite testSuite, Collection<CompiledRegexEntity> candidates, double accuracyThreshold) {
        this.safeExecutionContext = safeExecutionContext;
        this.testSuite = testSuite;
        this.candidates = candidates;
        // TODO this stuff needs to be added back in, but maybe it shouldn't happen in the constructor
        // Automaton truthAutomaton = new RegExp(testSuite.pattern()).toAutomaton(true);
        // SafeMatcher truthSafeMatcher = new SafeMatcher(Pattern.compile(testSuite.pattern()), safeExecutionContext);
        // this.truthLanguageApprox = LanguageApproximation.create(truthAutomaton, truthSafeMatcher);
        this.truthLanguageApprox = null;
        this.accuracyThreshold = accuracyThreshold;
    }

    @Override
    public Map<Long, Set<RegexTestSuiteSolution>> call() throws Exception {

        // truth tree
        // Tree truthRegexTree = AstDistance.buildTree(this.testSuite.pattern());

        Set<RegexTestSuiteSolution> hits = this.candidates.stream()
                .map(compiledRegexEntity -> {
                    IndeterminateBoolean fullMatchSatisfies = testSuite.hasPositiveAndNegativeStrings(SafeMatcher.MatchMode.FULL, 1)
                            ? IndeterminateBoolean.fromBoolean(regexSatisfiesTestSuiteFullMatch(compiledRegexEntity))
                            : IndeterminateBoolean.UNDETERMINED;

                    IndeterminateBoolean partialMatchSatisfies = testSuite.hasPositiveAndNegativeStrings(SafeMatcher.MatchMode.PARTIAL, 1)
                            ? IndeterminateBoolean.fromBoolean(regexSatisfiesTestSuitePartialMatch(compiledRegexEntity))
                            : IndeterminateBoolean.UNDETERMINED;

                    return new EvaluationResult(compiledRegexEntity, fullMatchSatisfies, partialMatchSatisfies);
                })
                // only interested in test suite results that are at least either a partial or full match
                .filter(result -> result.fullMatch().coerceToBoolean() || result.partialMatch().coerceToBoolean())
                .map(result -> {
                    // measure edit distance
                    int astDistance = -1;
                    /*
                    try {
                         astDistance = AstDistance.editDistance(truthRegexTree, result.entity().regexPattern().pattern());
                    } catch (ArrayIndexOutOfBoundsException | IOException exe) {
                        astDistance = -1;
                    }
                     */

                    // measure automaton distance
                    double fullESimilarity = Double.NaN;
                    double partialESimilarity = Double.NaN;
                    if (truthLanguageApprox != null) {
                        fullESimilarity = truthLanguageApprox.eSimilarity(result.entity().regexPattern(), SafeMatcher.MatchMode.FULL, safeExecutionContext);
                        partialESimilarity = truthLanguageApprox.eSimilarity(result.entity().regexPattern(), SafeMatcher.MatchMode.PARTIAL, safeExecutionContext);
                    }

                    return new RegexTestSuiteSolution(result.entity().id(),
                            result.entity().projectId(),
                            result.fullMatch(),
                            result.partialMatch(),
                            astDistance,
                            fullESimilarity,
                            partialESimilarity
                            );
                })
                .collect(Collectors.toSet());

        return Map.of(testSuite.id(), hits);
    }

    private boolean regexSatisfiesTestSuitePartialMatch(CompiledRegexEntity entity) {
        logger.debug("Testing test suite {} against regex {}", testSuite.id(), entity.id());

        SafeMatcher safeMatcher = new SafeMatcher(entity.regexPattern(), this.safeExecutionContext);

        int correctlyIdentified = 0;
        int idx = 0;
        int total = testSuite.strings().size();
        for (RegexTestSuiteString testSuiteString : testSuite.strings()) {

            // check if we should keep going
            int remaining = total - idx;
            idx += 1;
            if (noLongerAPossibleCandidate(correctlyIdentified, total, remaining)) {
                return false;
            }

            // determine if this regex partially matches the given string
            SafeMatcher.PartialMatchResult partialMatchResult;
            try {
                logger.trace("evaluating regex {} on test suite string {} of test suite {}", entity.id(), testSuiteString.id(), testSuite.id());
                Optional<SafeMatcher.PartialMatchResult> result = safeMatcher.partialMatch(testSuiteString.subject(), Duration.ofSeconds(2));
                if (result.isEmpty()) {
                    logger.debug("Timed out while matching, not a candidate");
                    continue;
                }
                partialMatchResult = result.get();
            } catch (StackOverflowError exe) {
                logger.debug("Could not evaluate regex {} on test suite string {} due to stack overflow", entity.id(), testSuiteString.id());
                continue;
            }

            if (!testSuiteString.matchStatus().partialMatch() && partialMatchResult.matchResult() != SafeMatcher.MatchResult.MATCH) {
                correctlyIdentified++;
                continue;
            }

            // at this point, the test suite string MUST be a positive partial match string

            if (partialMatchResult.matchResult() == SafeMatcher.MatchResult.NOT_MATCH) {
                // if it should not have matched but did,
                continue;
            }

            int actualStart = partialMatchResult.start();
            int actualEnd = partialMatchResult.end();

            if (actualStart != testSuiteString.matchStatus().partialMatchStartIdx() || actualEnd != testSuiteString.matchStatus().partialMatchEndIdx()) {
                logger.debug("Regex {} did not pull out the correct {} of test suite {}", entity.id(), testSuiteString.id(), testSuite.id());
                continue;
            }

            // if we got to here, then we correctly identified the same substring
            correctlyIdentified++;
        }

        // if we correctly identify all strings, accept
        double computedAccuracy = correctlyIdentified / (double) total;
        return computedAccuracy >= this.accuracyThreshold;
    }

    private boolean regexSatisfiesTestSuiteFullMatch(CompiledRegexEntity entity) {

        logger.debug("Testing test suite {} against regex {}", testSuite.id(), entity.id());

        SafeMatcher safeMatcher = new SafeMatcher(entity.regexPattern(), this.safeExecutionContext);

        int correctlyIdentified = 0;
        int idx = 0;
        int totalStrings = testSuite.strings().size();
        for (RegexTestSuiteString testSuiteString : testSuite.strings()) {

            // check if we should keep going
            int remaining = totalStrings - idx;
            idx += 1;
            if (noLongerAPossibleCandidate(correctlyIdentified, totalStrings, remaining)) {
                return false;
            }

            // determine if this regex partially matches the given string
            boolean fullMatches = false;
            try {
                logger.trace("evaluating regex {} on test suite string {} of test suite {}", entity.id(), testSuiteString.id(), testSuite.id());
                SafeMatcher.MatchResult result = safeMatcher.match(testSuiteString.subject(), SafeMatcher.MatchMode.FULL, Duration.ofSeconds(2));
                switch (result) {
                    case MATCH -> fullMatches = true;
                    case NOT_MATCH -> fullMatches = false;
                    case TIMEOUT -> {
                        continue;
                    }
                }
            } catch (StackOverflowError exe) {
                logger.debug("Could not evaluate regex {} on test suite string {} due to stack overflow", entity.id(), testSuiteString.id());
                continue;
            }

            if (testSuiteString.matchStatus().fullMatch() == fullMatches) {
                correctlyIdentified++;
            }
        }

        double computedAccuracy = correctlyIdentified / (double) totalStrings;

        return computedAccuracy >= this.accuracyThreshold;
    }

    private boolean noLongerAPossibleCandidate(int currentCorrect, int total, int remaining) {
        int ideallyCorrect = currentCorrect + remaining;
        double bestPossibleAccuracy = ideallyCorrect / (double) total;

        return !(bestPossibleAccuracy >= this.accuracyThreshold);
    }
}
