package edu.purdue.dualitylab.evaluation.evaluation;

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
 * Used to find regexes that works for a regex
 */
public class TestSuiteEvaluator implements Callable<Map<Long, Set<RegexTestSuiteSolution>>> {
    private static final Logger logger = LoggerFactory.getLogger(TestSuiteEvaluator.class);

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

    public TestSuiteEvaluator(ExecutorService safeExecutionContext, RegexTestSuite testSuite, Collection<CompiledRegexEntity> candidates) {
        this.safeExecutionContext = safeExecutionContext;
        this.testSuite = testSuite;
        this.candidates = candidates;
    }

    @Override
    public Map<Long, Set<RegexTestSuiteSolution>> call() throws Exception {
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
                .map(result -> new RegexTestSuiteSolution(result.entity().id(), result.entity().projectId(), result.fullMatch(), result.partialMatch()))
                .collect(Collectors.toSet());

        return Map.of(testSuite.id(), hits);
    }

    private boolean regexSatisfiesTestSuitePartialMatch(CompiledRegexEntity entity) {
        logger.debug("Testing test suite {} against regex {}", testSuite.id(), entity.id());

        SafeMatcher safeMatcher = new SafeMatcher(entity.regexPattern(), this.safeExecutionContext);

        for (RegexTestSuiteString testSuiteString : testSuite.strings()) {

            // determine if this regex partially matches the given string
            SafeMatcher.PartialMatchResult partialMatchResult;
            try {

                logger.trace("evaluating regex {} on test suite string {} of test suite {}", entity.id(), testSuiteString.id(), testSuite.id());
                Optional<SafeMatcher.PartialMatchResult> result = safeMatcher.partialMatch(testSuiteString.subject(), Duration.ofSeconds(2));
                if (result.isEmpty()) {
                    logger.debug("Timed out while matching, not a candidate");
                    return false;
                }
                partialMatchResult = result.get();
            } catch (StackOverflowError exe) {
                logger.debug("Could not evaluate regex {} on test suite string {} due to stack overflow", entity.id(), testSuiteString.id());
                return false;
            }

            if (!testSuiteString.matchStatus().partialMatch()) {
                if (partialMatchResult.matchResult() == SafeMatcher.MatchResult.MATCH) {
                    // if it should not have matched but did,
                    logger.debug("Regex {} matches negative test suite string {} of test suite {}", entity.id(), testSuiteString.id(), testSuite.id());
                    return false;
                } else {
                    // we correctly identified an incorrect match. Go to the next iteration
                    continue;
                }
            }

            // at this point, the test suite string MUST be a positive partial match string

            if (partialMatchResult.matchResult() == SafeMatcher.MatchResult.NOT_MATCH) {
                // if it should not have matched but did,
                logger.debug("Regex {} does not match positive test suite string {} of test suite {}", entity.id(), testSuiteString.id(), testSuite.id());
                return false;
            }

            int actualStart = partialMatchResult.start();
            int actualEnd = partialMatchResult.end();

            if (actualStart != testSuiteString.matchStatus().partialMatchStartIdx() || actualEnd != testSuiteString.matchStatus().partialMatchEndIdx()) {
                logger.debug("Regex {} did not pull out the correct {} of test suite {}", entity.id(), testSuiteString.id(), testSuite.id());
                return false;
            }

            // if we got to here, then we correctly identified the same substring
        }

        // if we correctly identify all strings, accept
        logger.debug("Regex {} satisfies test suite {}", entity.id(), testSuite.id());
        return true;
    }

    private boolean regexSatisfiesTestSuiteFullMatch(CompiledRegexEntity entity) {

        logger.debug("Testing test suite {} against regex {}", testSuite.id(), entity.id());

        SafeMatcher safeMatcher = new SafeMatcher(entity.regexPattern(), this.safeExecutionContext);

        for (RegexTestSuiteString testSuiteString : testSuite.strings()) {

            // determine if this regex partially matches the given string
            boolean fullMatches = false;
            try {

                logger.trace("evaluating regex {} on test suite string {} of test suite {}", entity.id(), testSuiteString.id(), testSuite.id());
                SafeMatcher.MatchResult result = safeMatcher.match(testSuiteString.subject(), SafeMatcher.MatchMode.FULL, Duration.ofSeconds(2));
                switch (result) {
                    case MATCH -> fullMatches = true;
                    case NOT_MATCH -> fullMatches = false;
                    case TIMEOUT -> {
                        logger.debug("Timed out while matching, not a candidate");
                        return false;
                    }
                }
            } catch (StackOverflowError exe) {
                logger.debug("Could not evaluate regex {} on test suite string {} due to stack overflow", entity.id(), testSuiteString.id());
                return false;
            }

            if (testSuiteString.matchStatus().fullMatch() && !fullMatches) {
                // if it should have matched but didn't, reject
                logger.debug("Regex {} does not match positive test suite string {} of test suite {}", entity.id(), testSuiteString.id(), testSuite.id());
                return false;
            } else if (!testSuiteString.matchStatus().fullMatch() && fullMatches) {
                // if it should not have matched but did,
                logger.debug("Regex {} matches negative test suite string {} of test suite {}", entity.id(), testSuiteString.id(), testSuite.id());
                return false;
            }
        }

        // if we correctly identify all strings, accept
        logger.debug("Regex {} satisfies test suite {}", entity.id(), testSuite.id());
        return true;
    }
}
