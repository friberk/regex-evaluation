package edu.institution.lab.evaluation.safematch;

import edu.institution.lab.evaluation.model.StringWithSubMatch;

import java.time.Duration;
import java.util.Optional;
import java.util.concurrent.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * The safe matcher is responsible for safely evaluating a string on a regex. It performs actual match operations on
 * a separate thread and allows us to time out or otherwise cancel the execution. It takes an executor service to
 * perform our operations in
 */
public class SafeMatcher {

    /**
     * How we are matching: full or partial match
     */
    public enum MatchMode {
        FULL,
        PARTIAL,
    }

    /**
     * Represents the result of the match operations. Can either match, not match, or timeout.
     */
    public enum MatchResult {
        MATCH,
        NOT_MATCH,
        TIMEOUT;

        public static MatchResult fromBoolean(boolean matches) {
            return matches ? MATCH : NOT_MATCH;
        }

        public boolean matches() {
            return this == MATCH;
        }

        public boolean mismatches() {
            return this == NOT_MATCH;
        }
    }

    /**
     * Determines if it's a partial match and also populates start/end with the specific substring that matches.
     * @param matchResult result of the operation
     * @param start sub-match start
     * @param end sub-match end
     */
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
     * @param pattern The pattern we want to use
     * @param safeMatchContext The execution context to evaluate this regex in
     */
    public SafeMatcher(Pattern pattern, ExecutorService safeMatchContext) {
        this.pattern = pattern;
        this.executorService = safeMatchContext;
    }

    /**
     * Determine this safe matcher matches the given substring with sub match. If the mode is full match, then the whole
     * string is evaluated. Otherwise, a sub-match is found and checked if it is the same as the truth.
     *
     * @param charSequence content to match
     * @param mode How to match
     * @param timeout Amount of time before timeout
     * @return Match result
     */
    public MatchResult match(CharSequence charSequence, MatchMode mode, Duration timeout) {
        Future<Boolean> matchResult = executorService.submit(matchTask(charSequence, mode));

        try {
            boolean result = matchResult.get(timeout.toMillis(), TimeUnit.MILLISECONDS);
            return MatchResult.fromBoolean(result);
        } catch (ExecutionException e) {
            throw new RuntimeException(e);
        } catch (InterruptedException | TimeoutException e) {
            // if it times out, cancel further execution
            matchResult.cancel(true);
            return MatchResult.TIMEOUT;
        }
    }

    /**
     * Determine this safe matcher matches the given substring with sub match. If the mode is full match, then the whole
     * string is evaluated. Otherwise, a sub-match is found and checked if it is the same as the truth.
     *
     * @param stringWithSubMatch content to match
     * @param mode How to match
     * @param timeout Amount of time before timeout
     * @return Match result
     */
    public MatchResult match(StringWithSubMatch stringWithSubMatch, MatchMode mode, Duration timeout) {
        if (mode == MatchMode.FULL) {
            return match(stringWithSubMatch.wholeString(), MatchMode.FULL, timeout);
        }

        Future<PartialMatchResult> matchResult = executorService.submit(partialMatchTask(stringWithSubMatch.wholeString()));

        try {
            PartialMatchResult result = matchResult.get(timeout.toMillis(), TimeUnit.MILLISECONDS);
            boolean matches = stringWithSubMatch.subMatchStart() == result.start() && stringWithSubMatch.subMatchEnd() == result.end();
            return MatchResult.fromBoolean(matches);
        } catch (ExecutionException e) {
            throw new RuntimeException(e);
        } catch (InterruptedException | TimeoutException e) {
            // if it times out, cancel further execution
            matchResult.cancel(true);
            return MatchResult.TIMEOUT;
        }
    }

    /**
     * Perform specifically a partial match operation. This will extract the potential matching submatch
     * @param charSequence The string to evaluate
     * @param timeout How long this can run for
     * @return The partial match result, or empty if timed out.
     */
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
