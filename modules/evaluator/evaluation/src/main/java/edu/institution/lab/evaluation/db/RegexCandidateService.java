package edu.institution.lab.evaluation.db;

import edu.institution.lab.evaluation.model.CandidateRegex;

import java.sql.SQLException;
import java.util.stream.Stream;

public interface RegexCandidateService {
    Stream<CandidateRegex> loadCandidateRegexes(long projectId) throws SQLException;
}
