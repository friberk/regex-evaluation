package edu.purdue.dualitylab.evaluation.evaluation;

import edu.purdue.dualitylab.evaluation.model.RegexTestSuite;
import edu.purdue.dualitylab.evaluation.model.RegexTestSuiteSolution;
import edu.purdue.dualitylab.evaluation.model.RegexTestSuiteString;
import edu.purdue.dualitylab.evaluation.safematch.SafeMatcher;
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
                .filter(this::regexSatisfiesTestSuite)
                .map(candidate -> new RegexTestSuiteSolution(candidate.id(), candidate.projectId()))
                .collect(Collectors.toSet());

        return Map.of(testSuite.id(), hits);
    }

    private boolean regexSatisfiesTestSuite(CompiledRegexEntity entity) {

        logger.debug("Testing test suite {} against regex {}", testSuite.id(), entity.id());

        SafeMatcher safeMatcher = new SafeMatcher(entity.regexPattern(), this.safeExecutionContext);

        for (RegexTestSuiteString testSuiteString : testSuite.strings()) {

            // determine if this regex partially matches the given string
            boolean partiallyMatches = false;
            try {
                logger.trace("evaluating regex {} on test suite string {} of test suite {}", entity.id(), testSuiteString.id(), testSuite.id());
                SafeMatcher.MatchResult result = safeMatcher.match(testSuiteString.subject(), SafeMatcher.MatchMode.PARTIAL, Duration.ofSeconds(2));
                switch (result) {
                    case MATCH -> partiallyMatches = true;
                    case NOT_MATCH -> partiallyMatches = false;
                    case TIMEOUT -> {
                        logger.debug("Timed out while matching, not a candidate");
                        return false;
                    }
                }
            } catch (StackOverflowError exe) {
                logger.debug("Could not evaluate regex {} on test suite string {} due to stack overflow", entity.id(), testSuiteString.id());
                return false;
            }

            if (testSuiteString.matchStatus().partialMatch() && !partiallyMatches) {
                // if it should have matched but didn't, reject
                logger.debug("Regex {} does not match positive test suite string {} of test suite {}", entity.id(), testSuiteString.id(), testSuite.id());
                return false;
            } else if (!testSuiteString.matchStatus().partialMatch() && partiallyMatches) {
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
