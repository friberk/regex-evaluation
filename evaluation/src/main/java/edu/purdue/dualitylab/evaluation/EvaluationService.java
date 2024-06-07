package edu.purdue.dualitylab.evaluation;

import edu.purdue.dualitylab.evaluation.db.RegexDatabaseClient;
import edu.purdue.dualitylab.evaluation.model.RegexTestSuite;
import edu.purdue.dualitylab.evaluation.model.RegexTestSuiteString;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.sql.SQLException;
import java.util.HashMap;
import java.util.Optional;
import java.util.Set;
import java.util.regex.Pattern;
import java.util.regex.PatternSyntaxException;
import java.util.stream.Collectors;
import java.util.stream.Stream;

public class EvaluationService {

    private static final Logger logger = LoggerFactory.getLogger(EvaluationService.class);

    private record CompiledRegexEntity(
            long id,
            Pattern regexPattern
    ) {

        /**
         * Try to compile a regex entity into a regex. Return empty optional if regex cannot be compiled
         * @param id Regex Entity Id
         * @param pattern Regex entity pattern
         * @return Filled optional if valid, or empty if there is a syntax error
         */
        static Optional<CompiledRegexEntity> tryCompile(long id, String pattern) {
            try {
                Pattern regexEntityPattern = Pattern.compile(pattern);
                return Optional.of(new CompiledRegexEntity(id, regexEntityPattern));
            } catch (PatternSyntaxException | StackOverflowError exe) {
                return Optional.empty();
            }
        }
    }

    private final RegexDatabaseClient databaseClient;
    private final TestSuiteService testSuiteService;

    public EvaluationService(RegexDatabaseClient databaseClient) {
        this.testSuiteService = new TestSuiteService(databaseClient);
        this.databaseClient = databaseClient;
    }

    public HashMap<Long, Set<Long>> evaluateTestSuites() throws SQLException {

        databaseClient.setupResultsTable();

        HashMap<Long, Set<Long>> testSuiteMatches = new HashMap<>();
        Stream<RegexTestSuite> testSuites = this.testSuiteService.loadRegexTestSuites();
        testSuites.forEach(testSuite -> {
            logger.info("Starting to evaluate test suite {}: projectId={}, regexId={}", testSuite.id(), testSuite.projectId(), testSuite.regexId());
            try {
                Set<Long> matches = evaluateTestSuite(testSuite);
                testSuiteMatches.put(testSuite.id(), matches);
                logger.info("Successfully evaluated and got {} match(es)", matches.size());
            } catch (SQLException exe) {
                logger.warn("Failure while trying to evaluate test suite {}", testSuite.id(), exe);
            }
        });

        return testSuiteMatches;
    }

    private Set<Long> evaluateTestSuite(RegexTestSuite testSuite) throws SQLException {
         return databaseClient.loadCandidateRegexes(testSuite.projectId())
                // compile each regex, filtering out those that don't compile
                .flatMap(entity -> CompiledRegexEntity.tryCompile(entity.id(), entity.pattern()).stream())
                // filter for only the regexes that satisfy the test suite
                .filter(compiledEntity -> this.regexSatisfiesTestSuite(testSuite, compiledEntity))
                // just save ids
                .map(CompiledRegexEntity::id)
                // save unique results
                .collect(Collectors.toSet());
    }

    private boolean regexSatisfiesTestSuite(RegexTestSuite testSuite, CompiledRegexEntity entity) {

        logger.debug("Testing test suite {} against regex {}", testSuite.id(), entity.id());

        for (RegexTestSuiteString testSuiteString : testSuite.strings()) {

            // determine if this regex partially matches the given string
            boolean partiallyMatches;
            try {
                logger.debug("evaluating regex {} on test suite string {} of test suite {}", entity.id(), testSuiteString.id(), testSuite.id());
                partiallyMatches = entity.regexPattern().matcher(testSuiteString.subject()).find();
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
        logger.debug("Regex {} satisfies test suite {}", testSuite.id(), entity.id());
        return true;
    }
}
