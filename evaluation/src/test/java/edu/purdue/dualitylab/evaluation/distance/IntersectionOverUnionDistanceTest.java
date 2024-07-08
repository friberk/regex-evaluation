package edu.purdue.dualitylab.evaluation.distance;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class IntersectionOverUnionDistanceTest extends BaseDistanceTestSuite {

    public IntersectionOverUnionDistanceTest() {
        super(new IntersectionOverUnionDistance());
    }

    @Test
    void apply_shouldGiveOne_forIdentical() {
        String left = "a+";
        String right = "a+";
        double expected = 1.0;

        testPatterns(left, right, expected);
    }

    @Test
    void apply_shouldGiveOne_forIdenticalSemanticsButDifferentPattern() {
        testPatterns("[abcdefg]", "[a-g]", 1.0);
    }

    @Test
    void apply_shouldGiveZero_forCompletelyDifferentPatterns() {
        testPatterns("a+", "b+", 0.0);
    }

    @Test
    void apply_shouldGiveZero_forComplelyDifferentPatterns2() {
        testPatterns("[abcdefg][hijk]", "[xyz]*[qrs]+", 0.0);
    }

    @Test
    void apply_shouldGiveZero_forComplelyDifferentPatterns3() {
        testPatterns("abc", "abd", 0.0);
    }

    @Test
    void apply_shouldCallSimilar_ifPatternsAreSimilar() {
        testPatterns("ab+", "ab*", 1.5);
    }
}