package edu.purdue.dualitylab.evaluation.safematch;

import org.junit.jupiter.api.Test;

import java.time.Duration;
import java.util.Optional;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.regex.Pattern;

import static org.junit.jupiter.api.Assertions.*;

class SafeMatcherTest {

    @Test
    void partialMatch_correctlyFindsPartialMatchSubString() {
        String fullString = "hello  world";
        int expectedStart = 5;
        int expectedEnd = 7;

        Pattern pattern = Pattern.compile("\\s+");

        ExecutorService executionContext = Executors.newSingleThreadExecutor();

        SafeMatcher safeMatcher = new SafeMatcher(pattern, executionContext);
        Optional<SafeMatcher.PartialMatchResult> result = safeMatcher.partialMatch(fullString, Duration.ofSeconds(30));
        assertTrue(result.isPresent());
        assertEquals(result.get().matchResult(), SafeMatcher.MatchResult.MATCH);
        assertEquals(result.get().start(), expectedStart);
        assertEquals(result.get().end(), expectedEnd);
    }

    @Test
    void partialMatch_correctly_doesNotFindSubstring() {
        String fullString = "helloworld";
        int expectedStart = -1;
        int expectedEnd = -1;

        Pattern pattern = Pattern.compile("\\s+");

        ExecutorService executionContext = Executors.newSingleThreadExecutor();

        SafeMatcher safeMatcher = new SafeMatcher(pattern, executionContext);
        Optional<SafeMatcher.PartialMatchResult> result = safeMatcher.partialMatch(fullString, Duration.ofSeconds(30));
        assertTrue(result.isPresent());
        assertEquals(result.get().matchResult(), SafeMatcher.MatchResult.NOT_MATCH);
        assertEquals(result.get().start(), expectedStart);
        assertEquals(result.get().end(), expectedEnd);
    }
}