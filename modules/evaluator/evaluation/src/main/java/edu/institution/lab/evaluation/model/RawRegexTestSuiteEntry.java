package edu.institution.lab.evaluation.model;

import edu.institution.lab.evaluation.db.DbField;

public record RawRegexTestSuiteEntry(
    @DbField(name = "regex_id") Long regexId,
    @DbField(name = "project_id") Long projectId,
    @DbField(name = "pattern") String pattern,
    @DbField(name = "source_usage_id") Long sourceUsageId,
    @DbField(name = "subject_project_id") Long subjectProjectId,
    @DbField(name = "subject") String subject,
    @DbField(name = "func") String func
) {
}
