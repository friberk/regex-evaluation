package edu.purdue.dualitylab.evaluation.internet;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import edu.purdue.dualitylab.evaluation.TestSuiteService;
import edu.purdue.dualitylab.evaluation.db.RegexDatabaseClient;
import edu.purdue.dualitylab.evaluation.evaluation.AutoCloseableExecutorService;
import edu.purdue.dualitylab.evaluation.evaluation.CompiledRegexEntity;
import edu.purdue.dualitylab.evaluation.evaluation.TestSuiteEvaluator;
import edu.purdue.dualitylab.evaluation.model.CandidateRegex;
import edu.purdue.dualitylab.evaluation.model.RegexTestSuiteSolution;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.sql.SQLException;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicLong;
import java.util.regex.Pattern;
import java.util.regex.PatternSyntaxException;
import java.util.stream.Collectors;
import java.util.stream.Stream;

public final class InternetEvaluationService {

    private static final Logger logger = LoggerFactory.getLogger(InternetEvaluationService.class);

    private static final long STACK_OVERFLOW_PROJECT_ID = 1;

    private static Optional<StackOverflowRegexPost> parseNDJsonLine(ObjectMapper mapper, String line) {
        try {
            StackOverflowRegexPost post = mapper.readValue(line, StackOverflowRegexPost.class);
            return Optional.of(post);
        } catch (JsonProcessingException e) {
            logger.warn("post line record could not be parsed, skipping", e);
            return Optional.empty();
        }
    }

    private static Optional<CompiledRegexEntity> tryCompileRegex(AtomicLong nextId, String pattern) {
        try {
            Pattern validRegex = Pattern.compile(pattern);
            // TODO give these things an ID
            return Optional.of(new CompiledRegexEntity(nextId.getAndIncrement(), STACK_OVERFLOW_PROJECT_ID, validRegex));
        } catch (PatternSyntaxException exe) {
            logger.warn("regex /{}/ has invalid syntax, skipping", pattern, exe);
            return Optional.empty();
        }
    }

    private final RegexDatabaseClient internetRegexDatabaseClient;
    private final TestSuiteService testSuiteService;
    private final ObjectMapper mapper;

    public InternetEvaluationService(RegexDatabaseClient internetRegexDatabaseClient, RegexDatabaseClient regexDatabaseClient) {
        this.internetRegexDatabaseClient = internetRegexDatabaseClient;
        this.testSuiteService = new TestSuiteService(regexDatabaseClient);
        this.mapper = new ObjectMapper();
    }

    public void evaluateInternetRegexes() throws SQLException, FileNotFoundException {

        // load internet regex candidates from database
        Collection<CompiledRegexEntity> candidates = internetRegexDatabaseClient.loadInternetCandidates()
                .flatMap(candidateRegex -> CompiledRegexEntity.tryCompile(candidateRegex).stream())
                .toList();

        // save these to a file
        Map<Long, Set<RegexTestSuiteSolution>> collectedTestSuites = new HashMap<>();
        try (AutoCloseableExecutorService safeExecutionContext = new AutoCloseableExecutorService(Executors.newFixedThreadPool(Runtime.getRuntime().availableProcessors()));
             AutoCloseableExecutorService jobExecutor = new AutoCloseableExecutorService(Executors.newWorkStealingPool(Runtime.getRuntime().availableProcessors()))) {

            CompletionService<Map<Long, Set<RegexTestSuiteSolution>>> jobExecutionContext = new ExecutorCompletionService<>(jobExecutor);

            // submit all test suites for evaluation on all candidate regexes
            AtomicLong jobCount = new AtomicLong(0);
            testSuiteService.loadRegexTestSuites()
                    .map(testSuite -> new TestSuiteEvaluator(safeExecutionContext, testSuite, candidates))
                    .peek((job) -> jobCount.getAndIncrement())
                    .forEach(jobExecutionContext::submit);

            for (long i = jobCount.get(); i > 0; i--) {
                Future<Map<Long, Set<RegexTestSuiteSolution>>> future = jobExecutionContext.take();
                Map<Long, Set<RegexTestSuiteSolution>> result = future.get();
                collectedTestSuites.putAll(result);
                logger.info("{}/{} test suites remaining", i - 1, jobCount.get());
            }
        } catch (ExecutionException | InterruptedException e) {
            throw new RuntimeException(e);
        }

        // save contents to a file
        logger.info("saving results...");
        internetRegexDatabaseClient.insertManyInternetTestSuiteResults(collectedTestSuites);
        logger.info("done");
    }

    public void loadCandidatesFromFileAndSave(File ndJsonPostsFile) throws FileNotFoundException, SQLException {
        logger.info("reading stackoverflow posts from {}", ndJsonPostsFile.getPath());
        internetRegexDatabaseClient.setupInternetRegexDatabase();
        Collection<StackOverflowRegexPost> regexPosts = loadStackOverflowPostsFromFile(ndJsonPostsFile)
                .map(post -> {
                    Set<String> updatedUniquePatterns = post.patternStream()
                            .map(RegexFixer::fixInternetRegex)
                            .collect(Collectors.toSet());

                    return post.withPatterns(updatedUniquePatterns);
                })
                .collect(Collectors.toSet());

        internetRegexDatabaseClient.insertManyStackOverflowRegexes(regexPosts);
    }

    private Stream<StackOverflowRegexPost> loadStackOverflowPostsFromFile(File stackOverflowPostsFile) throws FileNotFoundException {
        BufferedReader reader = new BufferedReader(new FileReader(stackOverflowPostsFile));
        return reader.lines()
                .map(String::trim)
                .flatMap(line -> line.isBlank() ? Stream.empty() : Stream.of(line))
                .peek(line -> logger.debug("parsing post object '{}'", line))
                .flatMap(line -> parseNDJsonLine(this.mapper, line).stream());
    }

    /**
     * read regex entities from a file and compile them
     * @param ndJsonPostsFiles The file to read from
     * @return A collection of valid, compiled candidate regex entities from the file
     * @throws FileNotFoundException if the provided file does not exist
     */
    private Collection<CompiledRegexEntity> loadCandidatesFromFile(File ndJsonPostsFiles) throws FileNotFoundException {
        AtomicLong patternIds = new AtomicLong(0);
        return loadStackOverflowPostsFromFile(ndJsonPostsFiles)
                .flatMap(StackOverflowRegexPost::patternStream)
                .distinct()
                .flatMap(uniquePattern -> tryCompileRegex(patternIds, uniquePattern).stream())
                .toList();
    }
}
