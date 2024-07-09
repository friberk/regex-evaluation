package edu.purdue.dualitylab.evaluation.model;

public record DistanceUpdateRecord(
        long testSuiteId,
        long regexId,
        int astDistance,
        double automatonDistance
) {
}
