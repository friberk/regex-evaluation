package edu.purdue.dualitylab.evaluation.distance;

import dk.brics.automaton.Automaton;
import dk.brics.automaton.GenerateStrings;
import edu.purdue.dualitylab.evaluation.TestSuiteService;
import edu.purdue.dualitylab.evaluation.db.RegexDatabaseClient;
import edu.purdue.dualitylab.evaluation.distance.ast.Tree;
import edu.purdue.dualitylab.evaluation.evaluation.AutoCloseableExecutorService;
import edu.purdue.dualitylab.evaluation.model.*;
import edu.purdue.dualitylab.evaluation.safematch.SafeMatcher;
import edu.purdue.dualitylab.evaluation.util.CoverageUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.sql.SQLException;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicLong;
import java.util.function.BiPredicate;
import java.util.function.Predicate;
import java.util.regex.Pattern;
import java.util.regex.PatternSyntaxException;
import java.util.stream.Collectors;

/**
 * Service responsible for compute distances between regexes
 */
public class UpdateDistancesService {

    private static final Logger logger = LoggerFactory.getLogger(UpdateDistancesService.class);

    /**
     * Basic callable to actually computes the distances between a truth regex and the candidates
     * @param candidateRow The candidate row
     * @param truthTree The AST of the truth regex
     * @param truthLanguageApprox The language approximation of the truth (for semantic distance)
     * @param safeMatchContext Safe match context
     */
    private record DistanceCalculatorTask(RawTestSuiteResultRow candidateRow,
                                          Tree truthTree,
                                          LanguageApproximation truthLanguageApprox,
                                          ExecutorService safeMatchContext) implements Callable<Optional<DistanceUpdateRecord>> {

        @Override
        public Optional<DistanceUpdateRecord> call() throws Exception {
            // first, build out the stuff we need for the candidate
            Optional<Tree> candidateTree = buildTree(candidateRow().candidateRegex());

            // compile the regex
            Pattern candidatePattern = null;
            try {
                candidatePattern = Pattern.compile(candidateRow().candidateRegex());
            } catch (PatternSyntaxException exe) {
            }

            // compute the AST distance
            int editDistance = -1;
            if (truthTree != null && candidateTree.isPresent()) {
                try {
                    editDistance = AstDistance.editDistance(truthTree(), candidateTree.get());
                } catch (ArrayIndexOutOfBoundsException ignored) {
                }
            }

            // compute the semantic distance
            double semanticDistance = Double.NaN;
            if (truthLanguageApprox != null && candidatePattern != null) {
                semanticDistance = truthLanguageApprox.eSimilarity(candidatePattern, SafeMatcher.MatchMode.FULL, safeMatchContext());
            }

            // only report a value if we actually have something to update
            if (editDistance == -1 && Double.isNaN(semanticDistance)) {
                return Optional.empty();
            }

            return Optional.of(new DistanceUpdateRecord(candidateRow.testSuiteId(), candidateRow().candidateRegexId(), editDistance, semanticDistance));
        }
    }

    private final RegexDatabaseClient databaseClient;
    private final TestSuiteService testSuiteService;
    /// Checks if we should compute the distance for any given regex. e.g., a regex is too big to compute AST distance
    private final Predicate<String> regexValidityChecker;
    /// Checks if we should compute distance between a pair of regexes. e.g., the regexes are of crazy different sizes.
    private final BiPredicate<String, String> relativeRegexValidityChecker;
    /// have two difference caches because the truth regex cache can be much smaller because we should process left whole
    /// chunk of the truth regex at the same time
    private final GenerateStrings.GenerateStringsConfiguration generateStringsConfiguration;

    public UpdateDistancesService(RegexDatabaseClient regexDatabaseClient, Predicate<String> regexValidityChecker, BiPredicate<String, String> relativeRegexValidityChecker) {
        this.databaseClient = regexDatabaseClient;
        this.testSuiteService = new TestSuiteService(regexDatabaseClient);
        this.regexValidityChecker = regexValidityChecker;
        this.relativeRegexValidityChecker = relativeRegexValidityChecker;
        this.generateStringsConfiguration = new GenerateStrings.GenerateStringsConfiguration(true, 3, 5);
    }

    public void computeAndInsertDistanceUpdateRecordsV3() throws SQLException {
        computeAndInsertDistanceUpdateRecordsV3(true, true);
    }

    public void computeAndInsertDistanceUpdateRecordsV3(boolean computeAstDistance, boolean computeSemanticDistance) throws SQLException {

        List<RegexTestSuite> regexTestSuites = testSuiteService.loadRegexTestSuites()
                .toList();

        Collection<DistanceUpdateRecord> updateRecords = new ArrayList<>();
        try (AutoCloseableExecutorService jobExecutor = new AutoCloseableExecutorService(Executors.newWorkStealingPool(Runtime.getRuntime().availableProcessors()));
             AutoCloseableExecutorService safeExecutionContext = new AutoCloseableExecutorService(Executors.newFixedThreadPool(Runtime.getRuntime().availableProcessors()))) {

            CompletionService<Optional<DistanceUpdateRecord>> completionService = new ExecutorCompletionService<>(jobExecutor);

            int collectedTestSuites = 0;
            for (RegexTestSuite testSuite : regexTestSuites) {

                logger.info("starting to process test suite {}", testSuite.id());

                // if truth regex is invalid, keep moving
                if (!regexValidityChecker.test(testSuite.pattern())) {
                    logger.info("skipping updating distances for test suite {}/{}: truth failed validity check", ++collectedTestSuites, regexTestSuites.size());
                    continue;
                }

                logger.info("staring to process test suite {}", testSuite.id());
                Optional<Tree> truthTreeOpt = Optional.empty();
                if (computeAstDistance) {
                    truthTreeOpt = buildTree(testSuite.pattern());
                    if (truthTreeOpt.isEmpty()) {
                        logger.info("skipping updating distances for test suite {}/{}: couldn't build tree for truth", ++collectedTestSuites, regexTestSuites.size());
                        continue;
                    }
                }

                LanguageApproximation truthLanguageApprox = null;
                if (computeSemanticDistance) {
                    Optional<Automaton> truthAutomaton = CoverageUtils.createAutomatonOptional(testSuite.pattern());
                    if (truthAutomaton.isEmpty()) {
                        logger.info("skipping updating distances for test suite {}/{}: failed to create truth automaton", ++collectedTestSuites, regexTestSuites.size());
                        continue;
                    }

                    // generate strings for the ground truth regex
                    try {
                        Set<String> truthPositiveStrings = GenerateStrings.generateStrings(truthAutomaton.get(), generateStringsConfiguration.withGeneratePositiveStrings(true));
                        Set<String> truthNegativeStrings = GenerateStrings.generateStrings(truthAutomaton.get(), generateStringsConfiguration.withGeneratePositiveStrings(false));

                        Set<StringWithSubMatch> updatedPositive = truthPositiveStrings.stream()
                                .map(str -> new StringWithSubMatch(str, 0, str.length()))
                                .collect(Collectors.toSet());

                        truthLanguageApprox = new LanguageApproximation(updatedPositive, truthNegativeStrings);
                    } catch (IllegalArgumentException exe) {
                        logger.info("skipping updating distances for test suite {}/{}: truth regex is syntactically invalid", ++collectedTestSuites, regexTestSuites.size());
                        continue;
                    } catch (OutOfMemoryError oom) {
                        logger.info("ran out of memory while approximating language for regex /{}/", testSuite.pattern());
                    }
                }

                if (truthTreeOpt.isEmpty() && truthLanguageApprox == null) {
                    logger.info("Neither AST nor semantic distances are being computed, so continuing");
                    continue;
                }


                // how that we have information about the truth, we can do stuff for each child
                AtomicLong submittedJobs = new AtomicLong();
                LanguageApproximation finalTruthLanguageApprox = truthLanguageApprox;
                Tree nullableTruthTree = truthTreeOpt.orElse(null);
                databaseClient.loadRawTestSuiteResults(testSuite.id())
                        // make sure that candidates pass checks
                        .filter(row -> regexValidityChecker.test(row.candidateRegex()) && relativeRegexValidityChecker.test(row.truthRegex(), row.candidateRegex()))
                        .map(row -> new DistanceCalculatorTask(row, nullableTruthTree, finalTruthLanguageApprox, safeExecutionContext))
                        .peek(_row -> submittedJobs.incrementAndGet())
                        .forEach(completionService::submit);

                for (long i = submittedJobs.get(); i > 0; i--) {
                    Future<Optional<DistanceUpdateRecord>> future = completionService.take();
                    Optional<DistanceUpdateRecord> result = future.get();
                    result.ifPresent(updateRecords::add);
                }

                logger.info("finished updating distances for test suite {}/{}", ++collectedTestSuites, regexTestSuites.size());
            }
        } catch (ExecutionException | InterruptedException e) {
            throw new RuntimeException(e);
        }

        // save everything
        logger.info("Updating distances in database");
        databaseClient.updateManyTestSuiteResultsDistances(updateRecords);
        logger.info("Successfully updated all distances");
    }

    private static Optional<Tree> buildTree(String pattern) {
        try {
            Tree truthRegexTree = AstDistance.buildTree(pattern);
            truthRegexTree.prepareForDistance();
            return Optional.of(truthRegexTree);
        } catch (OutOfMemoryError ignored) {
            // if we encounter one of these errors, then we should just skip edit distance
            logger.warn("failed to build tree for truth regex, so skipping AST measures for this test suite");
            return Optional.empty();
        }
    }
}
