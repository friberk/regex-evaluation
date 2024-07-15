package edu.purdue.dualitylab.evaluation.distance;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.*;

import java.io.IOException;
import java.util.function.Consumer;

public class AstDistanceTest {

    @Test
    void distance_shouldBeZero_forIdentical() throws IOException {
        testCase("a+", "a+", 0);
    }

    @Test
    void editDistance_shouldBeOne_forAddition() throws IOException {
        testCase("a+", "a*", 1);
    }

    @Test
    void editDistance_shouldBeTwo_forCharacterClasses() throws IOException {
        testCase("[a-z]", "[A-Z]", 2);
    }

    @Test
    void editDistance_shouldBeTwo_forCharacterClasses2() throws IOException {
        testCase("[a-z]", "[0-9]", 2);
    }

    @Test
    void editDistance_shouldHaveBigDiff_forDissimilarRegexes() throws IOException {
        testCase("[a-z]", "a+", 11);
    }

    private void testCase(String left, String right, int expectedDistance) throws IOException {
        testCase(left, right, (actual) -> assertThat(actual).isEqualTo(expectedDistance));
    }

    private void testCase(String left, String right, Consumer<Integer> tester) throws IOException {
        int actualDistance = AstDistance.editDistance(left, right);
        tester.accept(actualDistance);
    }
}
