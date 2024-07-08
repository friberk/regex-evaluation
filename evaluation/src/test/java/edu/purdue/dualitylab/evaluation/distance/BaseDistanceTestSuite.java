package edu.purdue.dualitylab.evaluation.distance;

import dk.brics.automaton.Automaton;

import java.util.function.Consumer;
import java.util.function.Predicate;

import static org.junit.jupiter.api.Assertions.assertEquals;

public abstract class BaseDistanceTestSuite {

    private final DistanceMeasure<Automaton> automatonDistance;
    private final DistanceMeasure<String> patternDistance;

    public BaseDistanceTestSuite(DistanceMeasure<Automaton> automatonDistance) {
        this.automatonDistance = automatonDistance;
        this.patternDistance = DistanceUtils.createStringDistanceMeasure(this.automatonDistance);
    }

    protected void testPatterns(String left, String right, double expected) {
        testPatterns(left, right, (actual) -> assertEquals(expected, actual));
    }

    protected void testPatterns(String left, String right, Consumer<Double> actualTester) {
        double actual = patternDistance.apply(left, right);
        actualTester.accept(actual);
    }
}
