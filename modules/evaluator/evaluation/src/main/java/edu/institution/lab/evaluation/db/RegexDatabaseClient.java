package edu.institution.lab.evaluation.db;

import dk.brics.automaton.AutomatonCoverage;
import edu.institution.lab.evaluation.internet.StackOverflowRegexPost;
import edu.institution.lab.evaluation.model.*;
import edu.institution.lab.evaluation.util.IndeterminateBoolean;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.*;
import java.sql.*;
import java.util.*;
import java.util.stream.Collectors;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;

/**
 * General client for interacting with the regex database. This class should contain all database operations that
 * are included in the project.
 */
public final class RegexDatabaseClient implements AutoCloseable, InternetRegexService {

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

    public Stream<RawRegexTestSuiteEntry> loadRawRegexTestSuites(int maxStringLength) throws SQLException {
        executeNamedQuery("create_candidate_regexes.sql");
        String queryText = loadNamedQuery("load_test_suites.sql").orElseThrow();
        PreparedStatement statement = connection.prepareStatement(queryText);
        statement.setInt(1, maxStringLength);
        return streamQuery(statement, RawRegexTestSuiteEntry.class);
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
                stringStmt.setInt(6, str.matchStatus().partialMatchStartIdx());
                stringStmt.setInt(7, str.matchStatus().partialMatchEndIdx());

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

    public void addDistanceColumnsToResults() throws SQLException {
        executedBatchNamedQuery("alter_results_similarity_columns.sql");
    }

    public Stream<RawTestSuiteResultRow> loadRawTestSuiteResults(long testSuiteId) throws SQLException {
        String queryText = loadNamedQuery("load_results_for_test_suite.sql").orElseThrow();
        PreparedStatement stmt = connection.prepareStatement(queryText);
        stmt.setLong(1, testSuiteId);
        return streamQuery(stmt, RawTestSuiteResultRow.class);
    }

    public void updateManyTestSuiteCoverages(Map<Long, AutomatonCoverage> coverages) throws SQLException {
        String queryText = loadNamedQuery("update_test_suite_coverages.sql").orElseThrow();
        PreparedStatement stmt = connection.prepareStatement(queryText);
        boolean oldAutoCommitStatus = connection.getAutoCommit();
        connection.setAutoCommit(false);

        for (Map.Entry<Long, AutomatonCoverage> update : coverages.entrySet()) {
            var fullCoverage = update.getValue().getFullMatchVisitationInfoSummary();
            var partialCoverage = update.getValue().getPartialMatchVisitationInfoSummary();

            int partialStart = storeCoverageSequentialColumns(stmt, 1, fullCoverage);
            storeCoverageSequentialColumns(stmt, partialStart, partialCoverage);

            stmt.setLong(7, update.getKey());

            stmt.execute();
        }

        connection.commit();
        connection.setAutoCommit(oldAutoCommitStatus);
        stmt.close();
    }

    public void updateManyRelativeCoverages(Collection<RelativeCoverageUpdate> updates) throws SQLException {
        String queryText = loadNamedQuery("update_test_suite_relative_coverage.sql").orElseThrow();
        PreparedStatement stmt = connection.prepareStatement(queryText);
        boolean oldAutoCommitStatus = connection.getAutoCommit();
        connection.setAutoCommit(false);

        for (RelativeCoverageUpdate update : updates) {
            var fullCoverage = update.fullCoverage();
            var partialCoverage = update.partialCoverage();

            int partialStart = storeCoverageSequentialColumns(stmt, 1, fullCoverage);
            storeCoverageSequentialColumns(stmt, partialStart, partialCoverage);

            stmt.setLong(7, update.testSuiteId());
            stmt.setLong(8, update.candidateRegexId());

            stmt.execute();
        }

        connection.commit();
        connection.setAutoCommit(oldAutoCommitStatus);
        stmt.close();
    }

    public Stream<RawTestSuiteResultRow> loadRawTestSuiteResultsForDistanceUpdate() throws SQLException {
        String queryText = loadNamedQuery("load_test_suite_results.sql").orElseThrow();
        return streamQuery(queryText, RawTestSuiteResultRow.class);
    }

    public void updateManyTestSuiteResultsDistances(Collection<DistanceUpdateRecord> distanceUpdateRecords) throws SQLException {
        String queryText = loadNamedQuery("update_result_distances.sql").orElseThrow();
        boolean oldAutoCommitStatus = connection.getAutoCommit();
        connection.setAutoCommit(false);
        PreparedStatement stmt = connection.prepareStatement(queryText);
        for (DistanceUpdateRecord record : distanceUpdateRecords) {
            stmt.setInt(1, record.astDistance());
            storeDoubleOrNullOnNonFinite(stmt, 2, record.automatonDistance());
            stmt.setLong(3, record.testSuiteId());
            stmt.setLong(4, record.regexId());

            stmt.execute();
        }

        connection.commit();
        connection.setAutoCommit(oldAutoCommitStatus);

        stmt.close();
    }

    public void insertManyTestSuiteResults(Map<Long, Set<RegexTestSuiteSolution>> testSuitesAndResults) throws SQLException {
        String queryText = loadNamedQuery("insert_test_suite_result.sql").orElseThrow();
        boolean oldAutoCommitStatus = connection.getAutoCommit();
        connection.setAutoCommit(false);
        PreparedStatement stmt = connection.prepareStatement(queryText);
        for (Map.Entry<Long, Set<RegexTestSuiteSolution>> entry : testSuitesAndResults.entrySet()) {
            long testSuiteId = entry.getKey();
            for (RegexTestSuiteSolution match : entry.getValue()) {
                stmt.setLong(1, testSuiteId);
                stmt.setLong(2, match.regexId());
                stmt.setLong(3, match.projectId());
                storeIndeterminateBoolean(stmt, 4, match.fullMatch());
                storeIndeterminateBoolean(stmt, 5, match.partialMatch());
                stmt.setInt(6, match.astDistance());
                storeDoubleOrNullOnNonFinite(stmt, 7, match.fullAutoDistance());
                storeDoubleOrNullOnNonFinite(stmt, 8, match.partialAutoDistance());

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
    public void setupInternetRegexDatabase() throws SQLException {
        executedBatchNamedQuery("create_internet_tables.sql");
    }

    public void insertManyStackOverflowRegexes(Collection<StackOverflowRegexPost> stackOverflowRegexPosts) throws SQLException {
        String queryText = loadNamedQuery("insert_internet_regex.sql").orElseThrow();
        boolean oldAutoCommitStatus = connection.getAutoCommit();
        connection.setAutoCommit(false);

        PreparedStatement stmt = connection.prepareStatement(queryText);
        for (StackOverflowRegexPost post : stackOverflowRegexPosts) {
            for (String pattern : post.patterns()) {
                stmt.setInt(1, StackOverflowRegexPost.STACK_OVERFLOW_ORIGIN_ID);
                stmt.setString(2, pattern);
                stmt.setString(3, post.uri());

                stmt.execute();
            }
        }

        connection.commit();
        connection.setAutoCommit(oldAutoCommitStatus);
        stmt.close();
    }

    @Override
    public Stream<CandidateRegex> loadInternetCandidates() throws SQLException {
        String queryText = loadNamedQuery("load_internet_regexes.sql").orElseThrow();
        return streamQuery(queryText, RawInternetRegex.class)
                .map(internetRegex -> new CandidateRegex(internetRegex.id(), internetRegex.originId(), internetRegex.pattern()));
    }

    @Override
    public void insertManyInternetTestSuiteResults(Map<Long, Set<RegexTestSuiteSolution>> solutions) throws SQLException {
        String queryText = loadNamedQuery("insert_internet_regex_solution.sql").orElseThrow();
        boolean oldAutoCommitStatus = connection.getAutoCommit();
        connection.setAutoCommit(false);
        PreparedStatement stmt = connection.prepareStatement(queryText);
        for (Map.Entry<Long, Set<RegexTestSuiteSolution>> entry : solutions.entrySet()) {
            long testSuiteId = entry.getKey();
            for (RegexTestSuiteSolution match : entry.getValue()) {
                stmt.setLong(1, testSuiteId);
                stmt.setLong(2, match.regexId());
                storeIndeterminateBoolean(stmt, 3, match.fullMatch());
                storeIndeterminateBoolean(stmt, 4, match.partialMatch());
                stmt.execute();
            }
        }
        connection.commit();
        connection.setAutoCommit(oldAutoCommitStatus);

        stmt.close();
    }

    public Stream<RawTestSuiteInternetRegexResultRow> loadTestSuiteInternetResults(long testSuiteId) throws SQLException {
        String queryText = loadNamedQuery("load_internet_results_for_test_suite.sql").orElseThrow();
        PreparedStatement stmt = connection.prepareStatement(queryText);
        stmt.setLong(1, testSuiteId);

        return streamQuery(stmt, RawTestSuiteInternetRegexResultRow.class);
    }

    @Override
    public void updateManyInternetTestSuiteResults(Collection<RelativeCoverageUpdate> updates) throws SQLException {
        String queryText = loadNamedQuery("update_internet_test_suite_coverage.sql").orElseThrow();
        boolean oldAutoCommitStatus = connection.getAutoCommit();
        connection.setAutoCommit(false);

        PreparedStatement stmt = connection.prepareStatement(queryText);

        for (RelativeCoverageUpdate match : updates) {
            int partialStart = storeCoverageSequentialColumns(stmt, 1, match.fullCoverage());
            storeCoverageSequentialColumns(stmt, partialStart, match.partialCoverage());
            stmt.setLong(7, match.testSuiteId());
            stmt.setLong(8, match.candidateRegexId());

            stmt.execute();
        }

        connection.commit();
        connection.setAutoCommit(oldAutoCommitStatus);
        stmt.close();
    }

    @Override
    public void close() throws Exception {
        connection.close();
    }

    /**
     * Executes query text and streams the rows.
     * @param queryText The query text to execute
     * @param clazz The row model type
     * @return Stream of rows
     * @param <T> The row type
     * @throws SQLException
     */
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

    /**
     * Takes a prepared statement, executes it, and streams the resulting rows. Each row is mapped into the provided
     * clazz type with the {@link edu.institution.lab.evaluation.db.EntityMapper} class.
     * @param stmt The statement to execute
     * @param clazz The row entity type.
     * @return A stream of rows
     * @param <T> The row entity type
     * @throws SQLException If there's a SQL issue.
     */
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

    /**
     * Execute a single named query without preparing the statement at all
     * @param namedQuery The name of the file that contains the query
     * @throws SQLException If there's a SQL issue
     */
    private void executeNamedQuery(String namedQuery) throws SQLException {
        String queryText = loadNamedQuery(namedQuery).orElseThrow();
        Statement stmt = connection.createStatement();
        stmt.execute(queryText);
        stmt.close();
    }

    /**
     * Executes a named query that contains multiple statements within. These contained SQL statements should be
     * ';' delimited
     * @param namedQuery The query file name to execute
     * @throws SQLException If there's a SQL issue
     */
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

    /**
     * Loads queries from the resource/sql directory. Basically, provide the file name, and this will attempt to load
     * the resource.
     * @param queryName The filename of the query you want to load
     * @return The query's text contents if the file was found, or empty optional if the file doesn't exist.
     */
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

    /**
     * Write a null value to the given column if the value is NaN or infinite.
     * @param stmt The statement for which we want to set the column
     * @param columnIdx The column index to set
     * @param value The double value to write. This value can be NaN or infinite
     * @throws SQLException Throws if there's a sql issue
     */
    private static void storeDoubleOrNullOnNonFinite(PreparedStatement stmt, int columnIdx, double value) throws SQLException {
        if (Double.isFinite(value)) {
            stmt.setDouble(columnIdx, value);
        } else {
            stmt.setNull(columnIdx, Types.DOUBLE);
        }
    }

    /**
     * Write an indeterminate boolean. If the value of the boolean is indeterminate, store null. Otherwise, store the
     * value of the boolean
     * @param stmt The statement of which we want to set the column
     * @param columnIndex The column index we want to set
     * @param ib The value
     * @throws SQLException Throws if there's an issue with sql
     */
    private static void storeIndeterminateBoolean(PreparedStatement stmt, int columnIndex, IndeterminateBoolean ib) throws SQLException {
        Optional<Boolean> optBool = ib.toOptionalBoolean();
        if (optBool.isPresent()) {
            stmt.setBoolean(columnIndex, optBool.get());
        } else {
            stmt.setNull(columnIndex, Types.BOOLEAN);
        }
    }

    /**
     * Convenience function for writing coverage to a database table. Coverage columns are typically adjacent, so this
     * simply perform a sequence of inserts that inserts the `coverageSummary` values.
     * @param stmt The statement to insert to
     * @param startingColumnIndex The column index of the node coverage column
     * @param coverageSummary The coverage summary to write
     * @return The next column after writing the coverage info. This is basically `startingColumnIdx + 3`
     * @throws SQLException If there's a SQL issue
     */
    private static int storeCoverageSequentialColumns(PreparedStatement stmt, int startingColumnIndex, AutomatonCoverage.VisitationInfoSummary coverageSummary) throws SQLException {
        storeDoubleOrNullOnNonFinite(stmt, startingColumnIndex, coverageSummary.getNodeCoverage());
        storeDoubleOrNullOnNonFinite(stmt, startingColumnIndex + 1, coverageSummary.getEdgeCoverage());
        storeDoubleOrNullOnNonFinite(stmt, startingColumnIndex + 2, coverageSummary.getEdgePairCoverage());
        return startingColumnIndex + 3;
    }
}
