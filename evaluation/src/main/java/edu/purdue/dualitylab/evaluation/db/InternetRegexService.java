package edu.purdue.dualitylab.evaluation.db;

import edu.purdue.dualitylab.evaluation.internet.StackOverflowRegexPost;
import edu.purdue.dualitylab.evaluation.model.CandidateRegex;
import edu.purdue.dualitylab.evaluation.model.RawTestSuiteInternetRegexResultRow;
import edu.purdue.dualitylab.evaluation.model.RegexTestSuiteSolution;
import edu.purdue.dualitylab.evaluation.model.RelativeCoverageUpdate;

import java.sql.SQLException;
import java.util.Collection;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Stream;

public interface InternetRegexService {
    void setupInternetRegexDatabase() throws SQLException;
    void insertManyStackOverflowRegexes(Collection<StackOverflowRegexPost> stackOverflowRegexPosts) throws SQLException;
    Stream<CandidateRegex> loadInternetCandidates() throws SQLException;
    void insertManyInternetTestSuiteResults(Map<Long, Set<RegexTestSuiteSolution>> solutions) throws SQLException;
    Stream<RawTestSuiteInternetRegexResultRow> loadTestSuiteInternetResults(long testSuiteId) throws SQLException;
    void updateManyInternetTestSuiteResults(Map<Long, Set<RelativeCoverageUpdate>> solutions) throws SQLException;
}
