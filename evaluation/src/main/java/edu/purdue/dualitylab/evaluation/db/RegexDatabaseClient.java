package edu.purdue.dualitylab.evaluation.db;

import edu.purdue.dualitylab.evaluation.model.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.sql.rowset.JoinRowSet;
import javax.sql.rowset.RowSetFactory;
import javax.sql.rowset.RowSetProvider;
import java.io.*;
import java.sql.*;
import java.util.Collection;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;

public final class RegexDatabaseClient implements AutoCloseable {

    private static final Logger logger = LoggerFactory.getLogger(RegexDatabaseClient.class);

    // connection to database
    private final Connection connection;
    private final ClassLoader queryLoader;

    public RegexDatabaseClient(Connection connection) {
        this.connection = connection;
        this.queryLoader = getClass().getClassLoader();
    }

    public void initDatabase(String extensionPath) throws SQLException {
        String initDatabaseQuery = loadNamedQuery("load_extensions.sql").orElseThrow();
        PreparedStatement stmt = connection.prepareStatement(initDatabaseQuery);
        stmt.setString(1, extensionPath);
        stmt.execute();
        stmt.close();
    }

    public Stream<RawRegexTestSuiteEntry> loadRawRegexTestSuites() throws SQLException {
        executeNamedQuery("create_candidate_regexes.sql");
        String queryText = loadNamedQuery("load_test_suites.sql").orElseThrow();
        return streamQuery(queryText, RawRegexTestSuiteEntry.class);
    }

    public void insertManyTestSuites(Collection<RegexTestSuite> testSuites) throws SQLException {
        executedBatchNamedQuery("prepare_test_suite_tables.sql");

        String insertTestSuiteText = loadNamedQuery("insert_test_suite.sql").orElseThrow();
        String insertString = loadNamedQuery("insert_test_suite_string.sql").orElseThrow();
        PreparedStatement testSuiteStmt = connection.prepareStatement(insertTestSuiteText, Statement.RETURN_GENERATED_KEYS);
        PreparedStatement stringStmt = connection.prepareStatement(insertString);

        boolean oldAutoCommit = connection.getAutoCommit();
        connection.setAutoCommit(false);

        for (RegexTestSuite testSuite : testSuites) {
            testSuiteStmt.setLong(1, testSuite.projectId());
            testSuiteStmt.setLong(2, testSuite.regexId());
            storeDoubleOrNullOnNonFinite(testSuiteStmt, 3, testSuite.fullMatchCoverage().getNodeCoverage());
            storeDoubleOrNullOnNonFinite(testSuiteStmt, 4, testSuite.fullMatchCoverage().getEdgeCoverage());
            storeDoubleOrNullOnNonFinite(testSuiteStmt, 5, testSuite.fullMatchCoverage().getEdgePairCoverage());
            storeDoubleOrNullOnNonFinite(testSuiteStmt, 6, testSuite.partialMatchCoverage().getNodeCoverage());
            storeDoubleOrNullOnNonFinite(testSuiteStmt, 7, testSuite.partialMatchCoverage().getEdgeCoverage());
            storeDoubleOrNullOnNonFinite(testSuiteStmt, 8, testSuite.partialMatchCoverage().getEdgePairCoverage());

            testSuiteStmt.executeUpdate();
            ResultSet generatedKeys = testSuiteStmt.getGeneratedKeys();
            int testSuiteKey;
            if (generatedKeys.next()) {
                testSuiteKey = generatedKeys.getInt(1);
            } else {
                throw new RuntimeException("Failed to get key of recently inserted test suite");
            }

            for (RegexTestSuiteString str : testSuite.strings()) {
                stringStmt.setLong(1, testSuiteKey);
                stringStmt.setString(2, str.subject());
                stringStmt.setString(3, str.func());
                stringStmt.setBoolean(4, str.matchStatus().fullMatch());
                stringStmt.setBoolean(5, str.matchStatus().partialMatch());

                stringStmt.executeUpdate();
            }
        }

        connection.commit();
        connection.setAutoCommit(oldAutoCommit);

        testSuiteStmt.close();
        stringStmt.close();
    }

    public void setupResultsTable() throws SQLException {
        executedBatchNamedQuery("create_test_suite_result_table.sql");
    }

    public void insertManyTestSuiteResults(Map<Long, Set<Long>> testSuitesAndResults) throws SQLException {
        String queryText = loadNamedQuery("insert_test_suite_result.sql").orElseThrow();
        boolean oldAutoCommitStatus = connection.getAutoCommit();
        connection.setAutoCommit(false);
        PreparedStatement stmt = connection.prepareStatement(queryText);
        for (Map.Entry<Long, Set<Long>> entry : testSuitesAndResults.entrySet()) {
            long testSuiteId = entry.getKey();
            for (long matchId : entry.getValue()) {
                stmt.setLong(1, testSuiteId);
                stmt.setLong(2, matchId);
                stmt.execute();
            }
        }
        connection.commit();
        connection.setAutoCommit(oldAutoCommitStatus);

        stmt.close();
    }

    public Stream<RawTestSuiteRow> loadRawTestSuiteRows() throws SQLException {
        String queryText = loadNamedQuery("load_existing_test_suites.sql").orElseThrow();
        return streamQuery(queryText, RawTestSuiteRow.class);
    }

    public Stream<CandidateRegex> loadCandidateRegexes(long projectId) throws SQLException {
        String queryText = loadNamedQuery("load_candidate_regexes.sql").orElseThrow();
        PreparedStatement stmt = connection.prepareStatement(queryText);
        stmt.setLong(1, projectId);
        return streamQuery(stmt, CandidateRegex.class);
    }

    @Override
    public void close() throws Exception {
        connection.close();
    }

    private <T> Stream<T> streamQuery(String queryText, Class<T> clazz) throws SQLException {
        UncheckedCloseable closable = null;
        try {
            Statement stmt = connection.createStatement();
            closable = UncheckedCloseable.wrap(stmt);
            ResultSet results = stmt.executeQuery(queryText);
            Stream<T> entityStream = StreamSupport.stream(new EntityStream<>(results, clazz), false);
            return entityStream.onClose(closable);
        } catch (SQLException exe) {
            if (closable != null) {
                try {
                    closable.close();
                } catch (Exception inner) {
                    exe.addSuppressed(inner);
                }
            }

            throw exe;
        }
    }

    private <T> Stream<T> streamQuery(PreparedStatement stmt, Class<T> clazz) throws SQLException {
        UncheckedCloseable closable = null;
        try {
            closable = UncheckedCloseable.wrap(stmt);
            ResultSet results = stmt.executeQuery();
            Stream<T> entityStream = StreamSupport.stream(new EntityStream<>(results, clazz), false);
            return entityStream.onClose(closable);
        } catch (SQLException exe) {
            if (closable != null) {
                try {
                    closable.close();
                } catch (Exception inner) {
                    exe.addSuppressed(inner);
                }
            }

            throw exe;
        }
    }

    private void executeNamedQuery(String namedQuery) throws SQLException {
        String queryText = loadNamedQuery(namedQuery).orElseThrow();
        Statement stmt = connection.createStatement();
        stmt.execute(queryText);
        stmt.close();
    }

    private void executedBatchNamedQuery(String namedQuery) throws SQLException {
        String queryText = loadNamedQuery(namedQuery).orElseThrow();

        Statement stmt = connection.createStatement();
        for (String batchQueryText : queryText.split(";")) {
            String trimmedQueryText = batchQueryText.trim();
            if (!trimmedQueryText.isBlank())
                stmt.addBatch(trimmedQueryText);
        }

        int[] results = stmt.executeBatch();
        logger.info("Executed {} commands", results.length);
        for (int idx = 0; idx < results.length; idx++) {
            if (results[idx] < 0) {
                logger.warn("While executing batch command: command {} failed with exit {}", idx, results[idx]);
            }
        }
        stmt.close();
    }

    private Optional<String> loadNamedQuery(String queryName) {
        String queryResourceName = String.format("sql/%s", queryName);
        InputStream queryInputStream = queryLoader.getResourceAsStream(queryResourceName);
        if (queryInputStream == null) {
            return Optional.empty();
        }

        StringWriter writer = new StringWriter();
        BufferedReader reader = new BufferedReader(new InputStreamReader(queryInputStream));
        try {
            reader.transferTo(writer);
            reader.close();
        } catch (IOException exe) {
            logger.error("error while reading query: {}", exe.toString());
            return Optional.empty();
        }

        return Optional.of(writer.toString());
    }

    private static void storeDoubleOrNullOnNonFinite(PreparedStatement stmt, int columnIdx, double value) throws SQLException {
        if (Double.isFinite(value)) {
            stmt.setDouble(columnIdx, value);
        } else {
            stmt.setNull(columnIdx, Types.DOUBLE);
        }
    }
}
