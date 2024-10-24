package edu.purdue.dualitylab.evaluation.util;

import dk.brics.automaton.Automaton;
import dk.brics.automaton.AutomatonCoverage;
import dk.brics.automaton.DfaBudgetExceededException;
import dk.brics.automaton.RegExp;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Duration;
import java.util.Optional;
import java.util.concurrent.ExecutorService;

public class CoverageUtils {

    private static final Logger logger = LoggerFactory.getLogger(CoverageUtils.class);

    public static Optional<AutomatonCoverage> createAutomatonCoverageOptional(String pattern) {
        return createAutomatonOptional(pattern)
                .map(AutomatonCoverage::new);
    }

    public static AutomatonCoverage createAutomatonCoverage(String pattern) {
        Automaton auto = createAutomaton(pattern);
        return new AutomatonCoverage(auto);
    }

    public static Optional<Automaton> createAutomatonCancellable(String pattern, ExecutorService safeExecutionContext, Duration timeout) {
        try {
            CancellableTask<Automaton> task = new CancellableTask<>(
                    safeExecutionContext,
                    () -> createAutomatonNullable(pattern),
                    timeout
            );

            return task.call();
        } catch (Exception exe) {
            // additionally wrap any execution exceptions
            return Optional.empty();
        }
    }

    public static Optional<Automaton> createAutomatonOptional(String pattern) {
        Automaton auto = createAutomatonNullable(pattern);
        return Optional.ofNullable(auto);
    }

    private static Automaton createAutomatonNullable(String pattern) {
        try {
            return createAutomaton(pattern);
        } catch (Throwable ignored) {
            return null;
        }
    }

    public static Automaton createAutomaton(String pattern) {
        try {
            logger.debug("compiling automaton for pattern /{}/...", pattern);
            RegExp regExp = new RegExp(pattern, RegExp.NONE);
            return regExp.toAutomaton();
        } catch (IllegalArgumentException exe) {
            logger.debug("Failed to compile automaton /{}/: {}", pattern, exe.getMessage());
            throw exe;
        } catch (DfaBudgetExceededException exe) {
            logger.debug("DFA budget exceeded for pattern /{}/: {}", pattern, exe.getMessage());
            throw exe;
        } catch (StackOverflowError so) {
            logger.debug("StackOverflow while building automaton for pattern /{}/: {}", pattern, so.getMessage());
            throw so;
        }
    }
}
