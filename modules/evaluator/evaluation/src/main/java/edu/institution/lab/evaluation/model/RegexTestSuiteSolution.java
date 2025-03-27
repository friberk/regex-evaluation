package edu.institution.lab.evaluation.model;

import edu.institution.lab.evaluation.util.IndeterminateBoolean;

/**
 * Represents a solution to a test suite
 * @param regexId The candidate regex id
 * @param projectId The project that originated this regex
 * @param fullMatch If it's a full match
 * @param partialMatch If it's a partial match
 * @param astDistance ASt distance to the truth
 * @param fullAutoDistance Full match semantic similarity
 * @param partialAutoDistance Partial match semantic similarity
 */
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
