package edu.purdue.dualitylab.evaluation.safematch;

import java.time.Duration;
import java.util.Optional;
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

    public record PartialMatchResult(
            MatchResult matchResult,
            int start,
            int end
    ) {
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
        Future<Boolean> matchResult = executorService.submit(matchTask(charSequence, mode));

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

    public Optional<PartialMatchResult> partialMatch(CharSequence charSequence, Duration timeout) {
        Future<PartialMatchResult> matchResult = executorService.submit(partialMatchTask(charSequence));

        try {
            PartialMatchResult result = matchResult.get(timeout.toMillis(), TimeUnit.MILLISECONDS);
            return Optional.of(result);
        } catch (ExecutionException e) {
            throw new RuntimeException(e);
        } catch (InterruptedException | TimeoutException e) {
            // if it times out, cancel further execution
            matchResult.cancel(true);
            return Optional.empty();
        }
    }

    private Callable<Boolean> matchTask(CharSequence charSequence, MatchMode mode) {
        return () -> {
            InterruptibleCharSequence interruptibleCharSequence = new InterruptibleCharSequence(charSequence);
            Matcher matcher = pattern.matcher(interruptibleCharSequence);
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
        };
    }

    private Callable<PartialMatchResult> partialMatchTask(CharSequence charSequence) {
        return () -> {
            InterruptibleCharSequence interruptibleCharSequence = new InterruptibleCharSequence(charSequence);
            Matcher matcher = pattern.matcher(interruptibleCharSequence);
            boolean matches;
            try {
                matches = matcher.find();
            } catch (StackOverflowError stackOverflowError) {
                return new PartialMatchResult(MatchResult.NOT_MATCH, -1, -1);
            }

            if (!matches) {
                return new PartialMatchResult(MatchResult.NOT_MATCH, -1, -1);
            }

            return new PartialMatchResult(MatchResult.MATCH, matcher.start(), matcher.end());
        };
    }
}
