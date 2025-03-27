package edu.institution.lab.evaluation.commands;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.datatype.jdk8.Jdk8Module;
import com.fasterxml.jackson.databind.DeserializationFeature;
import dk.brics.automaton.AutomatonCoverage;
import edu.institution.lab.evaluation.args.ManualQueryArgs;
import edu.institution.lab.evaluation.args.RootArgs;
import edu.institution.lab.evaluation.db.RegexDatabaseClient;
import edu.institution.lab.evaluation.evaluation.CompiledRegexEntity;
import edu.institution.lab.evaluation.model.ManualTestSuite;
import edu.institution.lab.evaluation.model.ManualTestSuiteResult;
import edu.institution.lab.evaluation.model.TestString;
import edu.institution.lab.evaluation.safematch.SafeMatcher;
import edu.institution.lab.evaluation.util.CoverageUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.sqlite.SQLiteConfig;

import java.io.*;
import java.sql.Connection;
import java.sql.DriverManager;
import java.time.Instant;
import java.time.Duration;
import java.util.Comparator;
import java.util.List;
import java.util.ArrayList;
import java.util.Optional;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.stream.Stream;
import java.util.HashMap;
import java.util.Map;

abstract class FullMatchManualTestSuiteMixIn {
    @JsonProperty("full_match_positive_strings")
    abstract List<String> positiveStrings();
    @JsonProperty("full_match_negative_strings")
    abstract List<String> negativeStrings();
    @JsonProperty("regex_id")
    abstract long regexId();
    @JsonProperty("project_id")
    abstract long projectId();
    @JsonProperty("test_suite_id")
    abstract long testSuiteId();
    @JsonProperty("regex_pattern")
    abstract Optional<String> regexPattern();
}

abstract class PartialMatchManualTestSuiteMixIn {
    @JsonProperty("partial_match_positive_strings")
    abstract List<String> positiveStrings();
    @JsonProperty("partial_match_negative_strings")
    abstract List<String> negativeStrings();
    @JsonProperty("regex_id")
    abstract long regexId();
    @JsonProperty("project_id")
    abstract long projectId();
    @JsonProperty("test_suite_id")
    abstract long testSuiteId();
    @JsonProperty("regex_pattern")
    abstract Optional<String> regexPattern();
}

/**
 * This command allows you to manually run a query. Use this for debugging purposes.
 */
public class ManualQueryCommand extends AbstractCommand<ManualQueryArgs, Void> {

    private static final Logger logger = LoggerFactory.getLogger(LoggerFactory.class);

    private final SQLiteConfig sqliteConfig;

    public ManualQueryCommand(RootArgs rootArgs, ManualQueryArgs args, SQLiteConfig config) {
        super(rootArgs, args);
        this.sqliteConfig = config;
    }

    @Override
    public Void call() throws Exception {

        String regexDbPath = String.format("jdbc:sqlite:%s", args.getDatabasePath());
        logger.info("Connecting to regex database at {}", regexDbPath);
        Connection regexConnection = DriverManager.getConnection(regexDbPath, this.sqliteConfig.toProperties());
        RegexDatabaseClient regexDatabaseClient = new RegexDatabaseClient(regexConnection);
        regexDatabaseClient.initDatabase(rootArgs.getExtensionPath());
        logger.info("Successfully connected to regex database");

        // pull regex entities
        ObjectMapper objectMapper = new ObjectMapper();
        objectMapper.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
        objectMapper.registerModule(new Jdk8Module());

        // Match mode
        boolean isFullMatch = args.getFullMatch();

        File inputFile = new File(args.getTestSuiteFile());
        File outputFile = new File(args.getOutputPath());
        int idx = 0;
        try (BufferedReader bufferedReader = new BufferedReader(new FileReader(inputFile));
             BufferedWriter bufferedWriter = new BufferedWriter(new FileWriter(outputFile, true))) { // Append mode

            logger.info("Reading NDJSON input from {}", inputFile.getPath());

            String line;
            while ((line = bufferedReader.readLine()) != null) {
                // Parse the NDJSON line into a ManualTestSuite
                logger.info("Processing NDJSON row: {}", ++idx);
                ManualTestSuite manualTestSuite = objectMapper.readValue(line, ManualTestSuite.class);

                List<String> positiveStrings = new ArrayList<>();
                List<String> negativeStrings = new ArrayList<>();

                for (TestString testString : manualTestSuite.strings()) {
                    boolean matches = isFullMatch ? testString.fullMatch() : testString.partialMatch();

                    if (matches) {
                        positiveStrings.add(testString.string());
                    } else {
                        negativeStrings.add(testString.string());
                    }
                }

                try {
                    // Start the timer
                    Instant startTime = Instant.now();

                    // Process the test suite and get candidates
                    List<ManualTestSuiteResult> candidates = processTestSuite(manualTestSuite, positiveStrings, negativeStrings, regexDatabaseClient);

                    // End the timer and calculate elapsed time in milliseconds
                    Instant endTime = Instant.now();
                    long elapsedTime = Duration.between(startTime, endTime).toMillis();

                    logger.info("Got {} candidates in {} ms", candidates.size(), elapsedTime);

                    // Prepare the output map
                    Map<String, Object> outputMap = new HashMap<String, Object>() {{
                        put("regex_id", manualTestSuite.regexId());
                        put("project_id", manualTestSuite.projectId());
                        put("test_suite_id", manualTestSuite.testSuiteId());
                        put("regex_pattern", manualTestSuite.regexPattern().orElse(null));
                        put("strings", manualTestSuite.strings());
                        put("candidates", candidates);
                        put("test_string_count", manualTestSuite.testStringCount());
                        put("elapsed_time", elapsedTime);
                    }};

                    // Write the list of candidates as a single NDJSON row (array format)
                    String outputLine = objectMapper.writeValueAsString(outputMap);
                    bufferedWriter.write(outputLine);
                    bufferedWriter.newLine(); // Add a newline after each JSON array
                    bufferedWriter.flush(); // Ensure the data is written immediately

                    logger.info("Wrote candidates to {}", outputFile.getPath());
                } catch (Exception e) {
                    logger.error("Error processing a row in NDJSON: {}", e.getMessage(), e);
                }
            }

        }

        logger.info("Finished processing all NDJSON rows. Results written to {}", outputFile.getPath());
        return null;
    }

    private List<ManualTestSuiteResult> processTestSuite(
            ManualTestSuite manualTestSuite,
            List<String> positiveStrings,
            List<String> negativeStrings,
            RegexDatabaseClient regexDatabaseClient
    ) throws Exception {

        ExecutorService safeExecutionContext = Executors.newWorkStealingPool();
        SafeMatcher.MatchMode matchMode = args.getFullMatch() ? SafeMatcher.MatchMode.FULL : SafeMatcher.MatchMode.PARTIAL;

        List<ManualTestSuiteResult> candidates = regexDatabaseClient.loadCandidateRegexes(-1)
                .flatMap(row -> CompiledRegexEntity.tryCompile(row).stream())
                .filter(compiledRegexEntity -> {
                    SafeMatcher matcher = new SafeMatcher(compiledRegexEntity.regexPattern(), safeExecutionContext);
                    for (String positive : positiveStrings) {
                        SafeMatcher.MatchResult result = matcher.match(positive, matchMode, Duration.ofSeconds(30));
                        if (!result.matches()) {
                            return false;
                        }
                    }

                    for (String negative : negativeStrings) {
                        SafeMatcher.MatchResult result = matcher.match(negative, matchMode, Duration.ofSeconds(30));
                        if (!result.mismatches()) {
                            return false;
                        }
                    }

                    return true;
                })
                .flatMap(compiledRegexEntity -> {
                    // get our automaton coverage
                    Optional<AutomatonCoverage> coverageOpt = CoverageUtils.createAutomatonCoverageOptional(compiledRegexEntity.regexPattern().pattern());
                    if (coverageOpt.isEmpty()) {
                        return Stream.empty();
                    }

                    // compute coverage
                    AutomatonCoverage coverage = coverageOpt.get();
                    positiveStrings.forEach(coverage::evaluate);
                    negativeStrings.forEach(coverage::evaluate);

                    return Stream.of(new ManualTestSuiteResult(compiledRegexEntity.id(), compiledRegexEntity.projectId(), compiledRegexEntity.regexPattern().pattern(), coverage.getFullMatchVisitationInfoSummary()));
                })
                .sorted(Comparator.comparingDouble(left -> left.fullCoverageSummary().getEdgeCoverage()))
                .toList();

        safeExecutionContext.shutdownNow();

        return candidates;
    }
}
