package edu.purdue.dualitylab.evaluation.model;

import java.util.Set;

public record RegexStringSet(
        long regexId,
        long projectId,
        String pattern,
        Set<RegexTestSuiteString> strings
) {
}
