package edu.purdue.dualitylab.evaluation.model;

import edu.purdue.dualitylab.evaluation.db.DbField;

public record CandidateRegex(
        @DbField(name = "id") Long id,
        @DbField(name = "project_id") Long projectId,
        @DbField(name = "pattern") String pattern
) {
}
