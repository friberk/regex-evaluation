package edu.purdue.dualitylab.evaluation.model;

import edu.purdue.dualitylab.evaluation.util.IndeterminateBoolean;

public record RegexTestSuiteSolution(
        long regexId,
        long projectId,
        IndeterminateBoolean fullMatch,
        IndeterminateBoolean partialMatch,
        int astDistance,
        double fullAutoDistance,
        double partialAutoDistance
) {
}
