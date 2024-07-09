package edu.purdue.dualitylab.evaluation.distance;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Assertions.*;

class OverhangSizeDistanceTest extends BaseDistanceTestSuite {

    public OverhangSizeDistanceTest() {
        super(new OverhangSizeDistance());
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
        testPatterns("ab+", "ab*", 0.5);
    }

    @Test
    void apply_shouldBeMoreThanHalfSimilar_forPrettyCloseRegexes() {
        testPatterns("ae*g+", "ae*g*", actual -> assertThat(actual).isGreaterThanOrEqualTo(0.5));
    }

    @Test
    void apply_shouldGiveZero_forComplelyDifferentPatterns4() {
        testPatterns("a*de+", "c*df*", 0.0);
    }

    @Test
    void apply_shouldGiveLessThanHalf_forMostlyDifferentRegexes() {
        testPatterns("a*de*", "c*df*", actual -> assertThat(actual).isLessThanOrEqualTo(0.5));
    }
}