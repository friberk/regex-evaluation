package edu.purdue.dualitylab.evaluation.distance;

import java.util.List;

public final class DistanceTestCases {
    public record DistanceTestCase(
            String left,
            String right,
            double expectedScore
    ) {}

    public static final List<DistanceTestCase> TEST_CASES = List.of(
            new DistanceTestCase("a+", "a+", 1.0),
            new DistanceTestCase("[abcdefg]", "[a-g]+", 1.0)
    );
}
