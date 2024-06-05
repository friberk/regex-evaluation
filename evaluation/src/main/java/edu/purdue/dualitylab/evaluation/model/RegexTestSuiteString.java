package edu.purdue.dualitylab.evaluation.model;

public record RegexTestSuiteString(
        String subject,
        Long projectId,
        String func,
        MatchStatus matchStatus
) {
    public static RegexTestSuiteString fromRaw(RawRegexTestSuiteEntry rawEntry) {
        return new RegexTestSuiteString(rawEntry.subject(), rawEntry.subjectProjectId(), rawEntry.func(), null);
    }

    public RegexTestSuiteString withMatchStatus(MatchStatus matchStatus) {
        return new RegexTestSuiteString(subject(), projectId(), func(), matchStatus);
    }
}
