package edu.purdue.dualitylab.evaluation.safematch;

import java.time.Duration;
import java.util.concurrent.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class SafeMatcher {

    public enum MatchMode {
        FULL,
        PARTIAL,
    }

    public enum MatchResult {
        MATCH,
        NOT_MATCH,
        TIMEOUT
    }

    private final Pattern pattern;
    private final ExecutorService executorService;

    /**
     * Take a pattern and produce a safe, timeout-able matcher
     * @param pattern
     * @param executorService
     */
    public SafeMatcher(Pattern pattern, ExecutorService executorService) {
        this.pattern = pattern;
        this.executorService = executorService;
    }

    public MatchResult match(CharSequence charSequence, MatchMode mode, Duration timeout) {
        // make a special sequence
        InterruptibleCharSequence interruptibleCharSequence = new InterruptibleCharSequence(charSequence);
        Matcher matcher = pattern.matcher(interruptibleCharSequence);
        Future<Boolean> matchResult = executorService.submit(() -> {
            boolean matches = false;
            try {
                switch (mode) {
                    case FULL -> matches = matcher.matches();
                    case PARTIAL -> matches = matcher.find();
                }
            } catch (StackOverflowError err) {
                return false;
            }

            return matches;
        });

        try {
            boolean result = matchResult.get(timeout.toMillis(), TimeUnit.MILLISECONDS);
            return result ? MatchResult.MATCH : MatchResult.NOT_MATCH;
        } catch (ExecutionException e) {
            throw new RuntimeException(e);
        } catch (InterruptedException | TimeoutException e) {
            // if it times out, cancel further execution
            matchResult.cancel(true);
            return MatchResult.TIMEOUT;
        }
    }
}
