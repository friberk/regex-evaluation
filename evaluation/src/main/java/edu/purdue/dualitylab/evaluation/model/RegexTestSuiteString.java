package edu.purdue.dualitylab.evaluation.model;

public record RegexTestSuiteString(
        Long id,
        String subject,
        Long projectId,
        String func,
        MatchStatus matchStatus
) {
    public static RegexTestSuiteString fromRaw(RawRegexTestSuiteEntry rawEntry) {
        return new RegexTestSuiteString(null, rawEntry.subject(), rawEntry.subjectProjectId(), rawEntry.func(), null);
    }

    public RegexTestSuiteString withMatchStatus(MatchStatus matchStatus) {
        return new RegexTestSuiteString(id(), subject(), projectId(), func(), matchStatus);
    }
}
