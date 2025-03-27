package edu.institution.lab.evaluation.model;

import edu.institution.lab.evaluation.db.DbField;

public record CandidateRegex(
        @DbField(name = "id") Long id,
        @DbField(name = "project_id") Long projectId,
        @DbField(name = "pattern") String pattern
) {
}
