package edu.purdue.dualitylab.evaluation.util;

import dk.brics.automaton.Automaton;
import dk.brics.automaton.AutomatonCoverage;
import dk.brics.automaton.DfaBudgetExceededException;
import dk.brics.automaton.RegExp;
import edu.purdue.dualitylab.evaluation.TestSuiteStatistics;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Optional;

public class CoverageUtils {

    private static Logger logger = LoggerFactory.getLogger(CoverageUtils.class);

    public static Optional<AutomatonCoverage> createAutomatonCoverageOptional(String pattern) {
        return createAutomatonOptional(pattern)
                .map(AutomatonCoverage::new);
    }

    public static AutomatonCoverage createAutomatonCoverage(String pattern) {
        Automaton auto = createAutomaton(pattern);
        return new AutomatonCoverage(auto);
    }

    public static Optional<Automaton> createAutomatonOptional(String pattern) {
        try {
            Automaton auto = createAutomaton(pattern);
            return Optional.of(auto);
        } catch (Throwable ignored) {
            return Optional.empty();
        }
    }

    public static Automaton createAutomaton(String pattern) {
        try {
            logger.debug("compiling automaton for pattern /{}/...", pattern);
            RegExp regExp = new RegExp(pattern, RegExp.NONE);
            return regExp.toAutomaton();
        } catch (IllegalArgumentException exe) {
            logger.warn("Failed to compile automaton /{}/: {}", pattern, exe.getMessage());
            throw exe;
        } catch (DfaBudgetExceededException exe) {
            logger.warn("DFA budget exceeded for pattern /{}/: {}", pattern, exe.getMessage());
            throw exe;
        } catch (StackOverflowError so) {
            logger.warn("StackOverflow while building automaton for pattern /{}/: {}", pattern, so.getMessage());
            throw so;
        }
    }
}
