package edu.institution.lab.evaluation.evaluation;

import dk.brics.automaton.Automaton;
import edu.institution.lab.evaluation.TestSuiteService;
import edu.institution.lab.evaluation.db.RegexDatabaseClient;
import edu.institution.lab.evaluation.distance.DistanceMeasure;
import edu.institution.lab.evaluation.model.RegexTestSuite;
import edu.institution.lab.evaluation.model.RegexTestSuiteSolution;
import edu.institution.lab.evaluation.model.RelativeCoverageUpdate;
import edu.institution.lab.evaluation.util.cache.AutomatonCache;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.sql.SQLException;
import java.time.Duration;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicLong;
import java.util.stream.Collectors;

public class EvaluationService {

    private static final Logger logger = LoggerFactory.getLogger(EvaluationService.class);

    private final RegexDatabaseClient databaseClient;
    private final TestSuiteService testSuiteService;

    public EvaluationService(RegexDatabaseClient databaseClient) {
        this.testSuiteService = new TestSuiteService(databaseClient);
        this.databaseClient = databaseClient;
    }

    public void evaluateAndSaveTestSuites() throws SQLException {

        databaseClient.setupResultsTable();

        /*
        The safe execution context is for safely matching a regex with a time constraint. Essentially, we run the
        matcher in a separate thread. That way, we can cancel it if it takes too long. We can also allow multiple
        evaluations to happen at the same time.

        The job executor is used to parallelize the evaluation process.
         */
        try (AutoCloseableExecutorService safeExecutionContext = new AutoCloseableExecutorService(Executors.newFixedThreadPool(Runtime.getRuntime().availableProcessors()));
             AutoCloseableExecutorService jobExecutor = new AutoCloseableExecutorService(Executors.newWorkStealingPool(Runtime.getRuntime().availableProcessors()))) {

            CompletionService<Map<Long, Set<RegexTestSuiteSolution>>> jobExecutionContext = new ExecutorCompletionService<>(jobExecutor);

            // load test suites
            Map<Long, List<RegexTestSuite>> projectTestSuites = testSuiteService.loadRegexTestSuites()
                    .collect(Collectors.groupingBy(RegexTestSuite::projectId));

            long totalTestSuites = projectTestSuites.values().stream().mapToInt(List::size).sum();

            AtomicLong totalCollectedTestSuites = new AtomicLong();

            // iterate over each project and its test suites, iterating as we go
            for (long projectId : projectTestSuites.keySet()) {
                List<RegexTestSuite> testSuites = projectTestSuites.get(projectId);

                // load a single set of candidate regexes for this project
                logger.info("Starting to evaluate test suites for project {}", projectId);
                List<CompiledRegexEntity> candidateEntities = databaseClient.loadCandidateRegexes(projectId)
                        .flatMap(candidate -> CompiledRegexEntity.tryCompile(candidate).stream())
                        .toList();

                // submit test suite evaluator jobs
                for (RegexTestSuite testSuite : testSuites) {
                    jobExecutionContext.submit(new TestSuiteEvaluator(safeExecutionContext, testSuite, candidateEntities, 1.00));
                }

                logger.info("Waiting on test suites...");

                // collect everything
                Map<Long, Set<RegexTestSuiteSolution>> collectedTestSuites = new HashMap<>();
                for (int i = testSuites.size(); i > 0; i--) {
                    Future<Map<Long, Set<RegexTestSuiteSolution>>> future = jobExecutionContext.take();
                    Map<Long, Set<RegexTestSuiteSolution>> result = future.get();
                    collectedTestSuites.putAll(result);
                    logger.info("{}/{} test suites from project {} remaining", i - 1, testSuites.size(), projectId);
                    totalCollectedTestSuites.incrementAndGet();
                }

                logger.info("Finished evaluating test suites for project {}", projectId);
                logger.info("Collected {}/{} total test suites", totalCollectedTestSuites.get(), totalTestSuites);

                logger.info("Saving test suites to database...");
                databaseClient.insertManyTestSuiteResults(collectedTestSuites);
                logger.info("Successfully saved to database");
            }
        } catch (SQLException | InterruptedException | ExecutionException e) {
            throw new RuntimeException(e);
        }
    }

    public void updateRelativeCoverages() {
        try (AutoCloseableExecutorService safeExecutionContext = new AutoCloseableExecutorService(Executors.newFixedThreadPool(Runtime.getRuntime().availableProcessors()));
             AutoCloseableExecutorService jobExecutor = new AutoCloseableExecutorService(Executors.newWorkStealingPool(Runtime.getRuntime().availableProcessors()))) {

            AutomatonCache automatonCache = new AutomatonCache(200, safeExecutionContext);
            CompletionService<RelativeCoverageUpdate> jobExecutionContext = new ExecutorCompletionService<>(jobExecutor);

            Map<Long, List<RegexTestSuite>> projectTestSuites = testSuiteService.loadRegexTestSuites()
                    .collect(Collectors.groupingBy(RegexTestSuite::projectId));

            long totalTestSuites = projectTestSuites.values().stream().mapToInt(List::size).sum();

            AtomicLong totalCollectedTestSuites = new AtomicLong();

            // iterate over each project and its test suites, iterating as we go
            for (long projectId : projectTestSuites.keySet()) {
                List<RegexTestSuite> testSuites = projectTestSuites.get(projectId);

                // load a single set of candidate regexes for this project
                logger.info("Starting to evaluate test suites for project {}", projectId);

                AtomicLong submittedTasks = new AtomicLong();
                for (RegexTestSuite testSuite : testSuites) {
                    databaseClient.loadRawTestSuiteResults(testSuite.id())
                            .flatMap(row -> automatonCache.getCachedOrTryCompile(row.candidateRegex(), Duration.ofMinutes(5)).stream()
                                    .map(automaton -> new RelativeCoverageEvaluator(testSuite, row, automaton)))
                            .peek((task) -> submittedTasks.incrementAndGet())
                            .forEach(jobExecutionContext::submit);
                }

                List<RelativeCoverageUpdate> batchUpdates = new ArrayList<>();
                long totalSubmittedTasks = submittedTasks.get();
                for (long i = 1; i <= totalSubmittedTasks; i++) {
                    Future<RelativeCoverageUpdate> future = jobExecutionContext.take();
                    RelativeCoverageUpdate update = future.get();
                    logger.debug("collected {}/{} tasks", i, totalSubmittedTasks);
                    batchUpdates.add(update);
                }

                databaseClient.updateManyRelativeCoverages(batchUpdates);

                long collected = totalCollectedTestSuites.addAndGet(testSuites.size());
                logger.info("finished processing {}/{} test suites", collected, totalTestSuites);
            }
        } catch (SQLException | InterruptedException | ExecutionException e) {
            throw new RuntimeException(e);
        }

        logger.info("successfully updated all relative coverages");
    }
}
