package edu.purdue.dualitylab.evaluation.util.cache;

import dk.brics.automaton.Automaton;
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
}