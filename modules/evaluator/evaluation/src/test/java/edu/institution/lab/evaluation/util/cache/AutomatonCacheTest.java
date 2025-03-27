package edu.institution.lab.evaluation.util.cache;

import dk.brics.automaton.Automaton;
import dk.brics.automaton.RegExp;
import dk.brics.automaton.TransitionTable;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.time.Duration;
import java.util.Optional;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Assertions.*;

class AutomatonCacheTest {

    ExecutorService compilationContext;
    AutomatonCache automatonCache;

    @BeforeEach
    void setup() {
        compilationContext = Executors.newSingleThreadExecutor();
        automatonCache = new AutomatonCache(5, compilationContext);
    }

    @Test
    void getCachedOrTryCompile_successfullyCachesRegex() {
        Optional<Automaton> compiledAutomaton = automatonCache.getCachedOrTryCompile("?(?:(a):)?(\\w{2,32}):(\\d{17,19})?", Duration.ofMinutes(1));
        assertThat(compiledAutomaton).isPresent();
    }

    @Test
    void sizeTest() {
        String pattern = "^(?:[a-z0-9_](?:[a-z0-9-_]{0,61}[a-z0-9])?\\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]$";
        RegExp regex = new RegExp(pattern);
        Automaton auto = regex.toAutomaton();
        assertThat(auto.getNumberOfStates() + auto.getNumberOfTransitions()).isEqualTo(1358);

        TransitionTable transitionTable = new TransitionTable(auto);
        assertThat(transitionTable.states().size()).isEqualTo(auto.getNumberOfStates());
    }
}