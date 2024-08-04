package edu.purdue.dualitylab.evaluation.util.cache;

import dk.brics.automaton.Automaton;
import dk.brics.automaton.DfaBudgetExceededException;
import dk.brics.automaton.RegExp;
import edu.purdue.dualitylab.evaluation.util.Pair;

import java.time.Duration;
import java.util.*;
import java.util.concurrent.*;
import java.util.regex.PatternSyntaxException;

/**
 * A specialized bounded cache for `Automaton`s. This cache optimizes for performance at the cost of memory. It works
 * by:
 * 1. evicting automata based on how long it takes to compile. If an automaton takes a long time to compile, then it
 * is cached for longer. Likewise, automata that compile quickly are evicted quickly because they are trivial to compile.
 * 2. A set of automata that cannot be compiled are cached. This is useful in the case where you are compiling patterns
 * in a loop and don't want to try to compile the same regex over and over
 */
public class AutomatonCache extends AbstractBoundedCache<String, Automaton, AutomatonCacheNode> {

    private record CompileAutomatonTask(String pattern) implements Callable<Optional<Pair<Automaton, Long>>> {
        @Override
        public Optional<Pair<Automaton, Long>> call() throws Exception {
            // first, parse the regex
            RegExp regExp;
            try {
                regExp = new RegExp(pattern);
            } catch (IllegalArgumentException exe) {
                // if parse fails, empty
                return Optional.empty();
            }

            // next start trying to compile the automaton
            Automaton automaton;
            long elapsedTime;
            try {
                long start = System.nanoTime();
                automaton = regExp.toAutomaton();
                long end = System.nanoTime();
                elapsedTime = end - start;
            } catch (DfaBudgetExceededException | StackOverflowError | OutOfMemoryError exe) {
                return Optional.empty();
            }

            return Optional.of(new Pair<>(automaton, elapsedTime));
        }
    }

    private final ExecutorService automatonCompilationContext;
    /// contains left set of patterns that we failed to compile into an automaton. Essentially, this is caching
    /// "you should not try to compile this because it will not succeed"
    private final Set<String> failedPatterns;

    public AutomatonCache(int maxSize, ExecutorService automatonCompilationContext) {
        this(maxSize, new HashMap<>(), automatonCompilationContext);
    }

    protected AutomatonCache(int maxSize, Map<String, AutomatonCacheNode> cacheImpl, ExecutorService automatonCompilationContext) {
        super(maxSize, cacheImpl);
        this.automatonCompilationContext = automatonCompilationContext;
        this.failedPatterns = new HashSet<>();
    }

    public boolean isFailedRegex(String pattern) {
        return failedPatterns.contains(pattern);
    }

    /**
     * Try to get the regex's automaton. If the automaton is not cached, or the regex has failed in the past, then
     * return null. Otherwise, the automaton
     * @param o The key to lookup
     * @return Automaton if cached. Null if failed or not found within
     */
    @Override
    public Automaton get(Object o) {
        if (!(o instanceof String) || failedPatterns.contains(o)) {
            return null;
        }

        return super.get(o);
    }

    /**
     * Caches the automaton for the given pattern. If an automaton is manually cached with this method, then it is
     * assumed to have infinitely long compilation time. The idea here is that, if you have a really, really, really
     * weird automaton that you want to "pin" in the cache, place it directly. MOST OF THE TIME YOU SHOULD USE
     * getCachedOrTryCompile
     * @param s Pattern to cache
     * @param automaton Automaton associated with that pattern
     * @return <TODO>fill this out</TODO>
     */
    @Override
    public Automaton put(String s, Automaton automaton) {
        return super.put(s, automaton);
    }

    /**
     * Main entry point to automaton cache. First, try to lookup if this pattern is already cached or failed. If it has,
     * then stop. Otherwise, it tries to compile the given pattern into an automaton with a timeout. If the automaton
     * fails to compile or times out, then the pattern is labelled as failed. If compilation succeeds, then it is cached
     * along with its compile time.
     *
     * @param regexPattern The pattern to try to compile
     * @param compilationTimeLimit Maximum amount of time allowed to attempt to compile
     * @return Automaton if success, or empty if failed to compile
     */
    public Optional<Automaton> getCachedOrTryCompile(String regexPattern, Duration compilationTimeLimit) {

        // if we already know that this pattern cannot compile, then return early
        if (failedPatterns.contains(regexPattern)) {
            return Optional.empty();
        }

        // if the regex is already cached, then just get it
        if (containsKey(regexPattern)) {
            Automaton existing = get(regexPattern);
            return Optional.of(Objects.requireNonNull(existing));
        }

        // otherwise, we need to actually compile this pattern
        Future<Optional<Pair<Automaton, Long>>> compilationTask = automatonCompilationContext.submit(new CompileAutomatonTask(regexPattern));
        Optional<Pair<Automaton, Long>> compiledAutomaton;
        try {
            compiledAutomaton = compilationTask.get(compilationTimeLimit.toMillis(), TimeUnit.MILLISECONDS);
        } catch (InterruptedException | ExecutionException e) {
            throw new RuntimeException(e);
        } catch (TimeoutException e) {
            compilationTask.cancel(true);
            compiledAutomaton = Optional.empty();
        }

        if (compiledAutomaton.isEmpty()) {
            // indicate that this failed to compile
            failedPatterns.add(regexPattern);
            return Optional.empty();
        }

        // actually cache
        Pair<Automaton, Long> automatonAndDuration = compiledAutomaton.get();
        AutomatonCacheNode cacheNode = new AutomatonCacheNode(automatonAndDuration.right(), automatonAndDuration.left());
        cacheImpl.put(regexPattern, cacheNode);
        return Optional.of(automatonAndDuration.left());
    }

    @Override
    protected AutomatonCacheNode wrapValue(Automaton value) {
        // if an automaton was provided specifically by the user, then pin it in place
        return new AutomatonCacheNode(Long.MAX_VALUE, value);
    }

    @Override
    protected String selectEvictKey() {
        // choose the pattern with the fasted build time
        return cacheImpl.entrySet().stream()
                .min(Entry.comparingByValue())
                .map(Entry::getKey)
                .orElseThrow();
    }
}
