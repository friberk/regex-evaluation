package edu.institution.lab.evaluation.commands;

import com.fasterxml.jackson.databind.ObjectMapper;
import edu.institution.lab.evaluation.TestSuiteService;
import edu.institution.lab.evaluation.TestSuiteStatistics;
import edu.institution.lab.evaluation.args.PullTestSuiteArgs;
import edu.institution.lab.evaluation.args.RootArgs;
import edu.institution.lab.evaluation.db.RegexDatabaseClient;
import edu.institution.lab.evaluation.evaluation.AutoCloseableExecutorService;
import edu.institution.lab.evaluation.model.RegexTestSuite;
import edu.institution.lab.evaluation.safematch.SafeMatcher;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.sqlite.SQLiteConfig;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.sql.Connection;
import java.sql.DriverManager;
import java.util.Collection;
import java.util.List;
import java.util.concurrent.Executors;

/**
 * Use this command to classify test suite strings as positive or negative strings. This command should be run before
 * the evaluation command.
 */
public class PullTestSuitesCommand extends AbstractCommand<PullTestSuiteArgs, Void> {

    private static final Logger logger = LoggerFactory.getLogger(PullTestSuitesCommand.class);

    private final SQLiteConfig sqliteConfig;

    public PullTestSuitesCommand(RootArgs rootArgs, PullTestSuiteArgs args, SQLiteConfig sqliteConfig) {
        super(rootArgs, args);
        this.sqliteConfig = sqliteConfig;
    }

    @Override
    public Void call() throws Exception {
        // connect to first argument
        // String dbPath = "jdbc:sqlite:/home/anonymous/backup/research/5-30-regexes/regexes-combined-10k.sqlite";
        String dbPath = String.format("jdbc:sqlite:%s", args.getDatabaseFile());
        logger.info("connecting to database at {}", dbPath);
        Connection connection = DriverManager.getConnection(dbPath, this.sqliteConfig.toProperties());
        RegexDatabaseClient regexDatabaseClient = new RegexDatabaseClient(connection);
        logger.info("Successfully connected to database");

        // String extensionPath = "/home/anonymous/backup/research/extractor/target/debug/libsqlite_regex_extensions.so";
        regexDatabaseClient.initDatabase(rootArgs.getExtensionPath());
        logger.info("Starting to load test suites...");
        TestSuiteService testSuiteService = new TestSuiteService(regexDatabaseClient);

        if (args.getUpdateCoverages()) {
            logger.info("just updating coverages");
            testSuiteService.updateTestSuiteCoverages();
            logger.info("successfully updated coverages");
            return null;
        }

        // String reportPath = "/home/anonymous/backup/research/5-30-regexes/test-suites.ndjson";
        TestSuiteStatistics testSuiteStatistics = new TestSuiteStatistics();

        List<RegexTestSuite> testSuites;
        try (
                AutoCloseableExecutorService safeExecutionContext = new AutoCloseableExecutorService(Executors.newSingleThreadExecutor())
                ) {

            int maxStringLength = args.getMaxStringLength().orElse(100);

            testSuites = testSuiteService
                    .createRegexTestSuitesFromRaw(maxStringLength, testSuiteStatistics, safeExecutionContext)
                    .toList();
        } catch (Exception e) {
            logger.error("Error while loading test suites", e);
            throw new RuntimeException(e);
        }

        logger.info("Saving {} test suites to original database...", testSuites.size());
        regexDatabaseClient.insertManyTestSuites(testSuites);
        logger.info("Saved to database");

        // this will only happen if args are set
        if (args.getJsonOutputPath().isPresent()) {
            saveTestSuitesToFile(args.getJsonOutputPath().get(), testSuites);
        }

        logger.info("Test suite stats: {}", testSuiteStatistics);

        regexDatabaseClient.close();
        logger.info("Done!");

        return null;
    }

    private void saveTestSuitesToFile(String path, Collection<RegexTestSuite> testSuites) throws IOException {
        String fullMatchTestSuites = String.format("%s.fullmatch", path);
        String partialMatchTestSuites = String.format("%s.partialmatch", path);
        File output = new File(fullMatchTestSuites);
        if (!output.exists()) {
            output.createNewFile();
        }
        BufferedWriter testSuiteWriter = new BufferedWriter(new FileWriter(output));
        ObjectMapper mapper = new ObjectMapper();

        logger.info("Writing full test suites to file {}", output.getCanonicalPath());
        testSuites.stream()
                .filter(regexTestSuite -> regexTestSuite.hasPositiveAndNegativeStrings(SafeMatcher.MatchMode.FULL, 1))
                .forEach(testSuite -> {
                    try {
                        String testSuiteLine = mapper.writeValueAsString(testSuite);
                        testSuiteWriter.write(testSuiteLine);
                        testSuiteWriter.newLine();
                    } catch (IOException e) {
                        throw new RuntimeException(e);
                    }
                });

        testSuiteWriter.flush();
        testSuiteWriter.close();

        File partialOutput = new File(partialMatchTestSuites);
        if (!partialOutput.exists()) {
            partialOutput.createNewFile();
        }
        BufferedWriter partialTestSuiteWriter = new BufferedWriter(new FileWriter(partialOutput));

        logger.info("Writing partial test suites to file {}", partialOutput.getCanonicalPath());
        testSuites.stream()
                .filter(regexTestSuite -> regexTestSuite.hasPositiveAndNegativeStrings(SafeMatcher.MatchMode.PARTIAL, 1))
                .forEach(testSuite -> {
                    try {
                        String testSuiteLine = mapper.writeValueAsString(testSuite);
                        partialTestSuiteWriter.write(testSuiteLine);
                        partialTestSuiteWriter.newLine();
                    } catch (IOException e) {
                        throw new RuntimeException(e);
                    }
                });

        partialTestSuiteWriter.flush();
        partialTestSuiteWriter.close();
    }
}
