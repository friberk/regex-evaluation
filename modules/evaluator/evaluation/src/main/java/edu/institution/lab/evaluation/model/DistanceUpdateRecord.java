package edu.institution.lab.evaluation.model;

public record DistanceUpdateRecord(
        long testSuiteId,
        long regexId,
        int astDistance,
        double automatonDistance
) {
}
