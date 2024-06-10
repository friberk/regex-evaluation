package edu.purdue.dualitylab.evaluation.evaluation;

import edu.purdue.dualitylab.evaluation.TestSuiteService;
import edu.purdue.dualitylab.evaluation.db.RegexDatabaseClient;
import edu.purdue.dualitylab.evaluation.model.RegexTestSuite;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.sql.SQLException;
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

    public Map<Long, Set<Long>> evaluateTestSuites() throws SQLException {

        databaseClient.setupResultsTable();

        ExecutorService safeExecutionContext = Executors.newFixedThreadPool(Runtime.getRuntime().availableProcessors());
        ExecutorService jobExecutor = Executors.newFixedThreadPool(Runtime.getRuntime().availableProcessors());
        CompletionService<Map<Long, Set<Long>>> jobExecutionContext = new ExecutorCompletionService<>(jobExecutor);

        Map<Long, Set<Long>> testSuiteResults = new HashMap<>();

        Map<Long, List<RegexTestSuite>> projectTestSuites = testSuiteService.loadRegexTestSuites()
                .collect(Collectors.groupingBy(RegexTestSuite::projectId));

        long totalTestSuites = projectTestSuites.values().stream().mapToInt(List::size).sum();

        AtomicLong totalCollectedTestSuites = new AtomicLong();
        projectTestSuites
                .forEach((projectId, testSuites) -> {
                    // load a single set of candidate regexes for this project
                    logger.info("Starting to evaluate test suites for project {}", projectId);
                    try {
                        List<CompiledRegexEntity> candidateEntities = databaseClient.loadCandidateRegexes(projectId)
                                .flatMap(candidate -> CompiledRegexEntity.tryCompile(candidate).stream())
                                .toList();

                        for (RegexTestSuite testSuite : testSuites) {
                            jobExecutionContext.submit(new TestSuiteEvaluator(safeExecutionContext, testSuite, candidateEntities));
                        }

                        logger.info("Waiting on test suites...");

                        // collect everything
                        for (int i = testSuites.size(); i > 0; i--) {
                            Future<Map<Long, Set<Long>>> future = jobExecutionContext.take();
                            Map<Long, Set<Long>> result = future.get();
                            testSuiteResults.putAll(result);
                            logger.info("{}/{} test suites from project {} remaining", i - 1, testSuites.size(), projectId);
                            totalCollectedTestSuites.incrementAndGet();
                        }

                        logger.info("Finished evaluating test suites for project {}", projectId);
                        logger.info("Collected {}/{} total test suites", totalCollectedTestSuites.get(), totalTestSuites);

                    } catch (SQLException | InterruptedException | ExecutionException e) {
                        throw new RuntimeException(e);
                    }
                });

        safeExecutionContext.shutdown();
        jobExecutor.shutdown();
        try {
            boolean success = jobExecutor.awaitTermination(5, TimeUnit.MINUTES);
            if (!success) {
                jobExecutor.shutdownNow();
            }

            success = safeExecutionContext.awaitTermination(5, TimeUnit.MINUTES);
            if (!success) {
                safeExecutionContext.shutdownNow();
            }
        } catch (InterruptedException e) {
            throw new RuntimeException(e);
        }

        return testSuiteResults;
    }
}
