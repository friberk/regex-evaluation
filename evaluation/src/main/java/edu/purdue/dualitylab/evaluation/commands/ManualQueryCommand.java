package edu.purdue.dualitylab.evaluation.commands;

import com.fasterxml.jackson.databind.ObjectMapper;
import dk.brics.automaton.AutomatonCoverage;
import edu.purdue.dualitylab.evaluation.args.ManualQueryArgs;
import edu.purdue.dualitylab.evaluation.args.RootArgs;
import edu.purdue.dualitylab.evaluation.db.RegexDatabaseClient;
import edu.purdue.dualitylab.evaluation.evaluation.CompiledRegexEntity;
import edu.purdue.dualitylab.evaluation.model.ManualTestSuite;
import edu.purdue.dualitylab.evaluation.model.ManualTestSuiteResult;
import edu.purdue.dualitylab.evaluation.safematch.SafeMatcher;
import edu.purdue.dualitylab.evaluation.util.CoverageUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.sqlite.SQLiteConfig;

import java.io.File;
import java.io.IOException;
import java.sql.Connection;
import java.sql.DriverManager;
import java.time.Duration;
import java.util.Comparator;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.stream.Collectors;
import java.util.stream.Stream;

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
        logger.info("connecting to regex database at ");
        Connection regexConnection = DriverManager.getConnection(regexDbPath, this.sqliteConfig.toProperties());
        RegexDatabaseClient regexDatabaseClient = new RegexDatabaseClient(regexConnection);
        regexDatabaseClient.initDatabase(rootArgs.getExtensionPath());
        logger.info("Successfully connected to regex database");

        // pull regex entities
        ObjectMapper objectMapper = new ObjectMapper();
        ManualTestSuite manualTestSuite = readTestSuite(objectMapper, args.getTestSuiteFile());

        logger.info("Starting to find candidates...");

        ExecutorService safeExecutionContext = Executors.newWorkStealingPool();

        SafeMatcher.MatchMode matchMode = args.getFullMatch() ? SafeMatcher.MatchMode.FULL : SafeMatcher.MatchMode.PARTIAL;

        List<ManualTestSuiteResult> candidates = regexDatabaseClient.loadCandidateRegexes(-1)
                .flatMap(row -> CompiledRegexEntity.tryCompile(row).stream())
                .filter(compiledRegexEntity -> {
                    SafeMatcher matcher = new SafeMatcher(compiledRegexEntity.regexPattern(), safeExecutionContext);
                    for (String positive : manualTestSuite.positiveStrings()) {
                        SafeMatcher.MatchResult result = matcher.match(positive, matchMode, Duration.ofSeconds(30));
                        if (!result.matches()) {
                            return false;
                        }
                    }

                    for (String negative : manualTestSuite.negativeStrings()) {
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
                    manualTestSuite.positiveStrings().forEach(coverage::evaluate);
                    manualTestSuite.negativeStrings().forEach(coverage::evaluate);

                    return Stream.of(new ManualTestSuiteResult(compiledRegexEntity.id(), compiledRegexEntity.projectId(), compiledRegexEntity.regexPattern().pattern(), coverage.getFullMatchVisitationInfoSummary()));
                })
                .sorted(Comparator.comparingDouble(left -> left.fullCoverageSummary().getEdgeCoverage()))
                .toList();

        logger.info("Got {} candidates", candidates.size());

        File outputFile = new File(args.getOutputPath());
        objectMapper.writeValue(outputFile, candidates);

        logger.info("Wrote candidates to {}", outputFile.getPath());

        safeExecutionContext.shutdownNow();

        return null;
    }

    private ManualTestSuite readTestSuite(ObjectMapper mapper, String path) throws IOException {
        File testSuiteFile = new File(path);
        return mapper.readValue(testSuiteFile, ManualTestSuite.class);
    }
}
