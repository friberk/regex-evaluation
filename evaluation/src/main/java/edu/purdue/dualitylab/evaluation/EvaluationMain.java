package edu.purdue.dualitylab.evaluation;

import com.fasterxml.jackson.databind.ObjectMapper;
import edu.purdue.dualitylab.evaluation.db.RegexDatabaseClient;
import edu.purdue.dualitylab.evaluation.model.RegexTestSuite;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.sqlite.SQLiteConfig;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.sql.*;
import java.util.List;
import java.util.concurrent.atomic.AtomicLong;

public class EvaluationMain {

    private final static Logger logger = LoggerFactory.getLogger(EvaluationMain.class);

    public static void main(String[] args) throws Exception {

        // connect to first argument
        String dbPath = "jdbc:sqlite:/home/charlie/backup/research/5-30-regexes/regexes-combined-10k.sqlite";
        Connection connection = DriverManager.getConnection(dbPath, sqliteConfig().toProperties());
        RegexDatabaseClient regexDatabaseClient = new RegexDatabaseClient(connection);
        logger.info("Successfully connected to database");

        String extensionPath = "/home/charlie/backup/research/regex-extractor-v2/target/debug/libsqlite_regex_extensions.so";
        regexDatabaseClient.initDatabase(extensionPath);
        logger.info("Starting to load test suites...");
        TestSuiteService testSuiteService = new TestSuiteService(regexDatabaseClient);

        File output = new File("/home/charlie/backup/research/5-30-regexes/test-suites.ndjson");
        if (!output.exists()) {
            output.createNewFile();
        }
        BufferedWriter testSuiteWriter = new BufferedWriter(new FileWriter(output));
        ObjectMapper mapper = new ObjectMapper();
        AtomicLong processedTestSuites = new AtomicLong();
        TestSuiteStatistics testSuiteStatistics = new TestSuiteStatistics();
        List<RegexTestSuite> testSuites = testSuiteService
                .loadRegexTestSuites(testSuiteStatistics)
                .toList();

        logger.info("Saving {} test suites to original database...", testSuites.size());
        regexDatabaseClient.insertManyTestSuites(testSuites);
        logger.info("Saved to database");

        logger.info("Writing test suites to file {}", output.getCanonicalPath());
        testSuites
                .forEach(testSuite -> {
                    try {
                        String testSuiteLine = mapper.writeValueAsString(testSuite);
                        testSuiteWriter.write(testSuiteLine);
                        testSuiteWriter.newLine();
                        processedTestSuites.addAndGet(1);
                    } catch (IOException e) {
                        throw new RuntimeException(e);
                    }
                });

        testSuiteWriter.flush();
        testSuiteWriter.close();
        logger.info("Successfully saved to database");

        logger.info("Test suite stats: {}", testSuiteStatistics);

        regexDatabaseClient.close();
        logger.info("Done!");
    }

    public static SQLiteConfig sqliteConfig() {
        SQLiteConfig config = new SQLiteConfig();
        config.enableLoadExtension(true);
        config.setSynchronous(SQLiteConfig.SynchronousMode.OFF);
        return config;
    }
}
