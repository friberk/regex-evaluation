package edu.institution.lab.evaluation.db;

import edu.institution.lab.evaluation.internet.StackOverflowRegexPost;
import edu.institution.lab.evaluation.model.CandidateRegex;
import edu.institution.lab.evaluation.model.RawTestSuiteInternetRegexResultRow;
import edu.institution.lab.evaluation.model.RegexTestSuiteSolution;
import edu.institution.lab.evaluation.model.RelativeCoverageUpdate;

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
    void updateManyInternetTestSuiteResults(Collection<RelativeCoverageUpdate> updates) throws SQLException;
}
