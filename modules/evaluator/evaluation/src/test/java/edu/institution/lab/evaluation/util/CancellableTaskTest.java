package edu.institution.lab.evaluation.util;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

import java.time.Duration;
import java.util.Optional;
import java.util.Random;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class CancellableTaskTest {

    ExecutorService executionContext;

    @BeforeEach
    void beforeEach() {
        executionContext = Executors.newSingleThreadExecutor();
    }

    @AfterEach
    void afterEach() {
        executionContext.shutdownNow();
    }

    @Test
    public void call_returnsValue_whenTaskCompletes() throws Exception {
        CancellableTask<Long> spinnyTask = new CancellableTask<>(executionContext, () -> {
            long result = 0;
            for (int i = 0; i < 100; i++) {
                result += 1;
            }

            return result;
        }, Duration.ofSeconds(20));

        Optional<Long> result = spinnyTask.call();
        assertTrue(result.isPresent());
        assertEquals(100L, result.get());
    }

    @Test
    public void call_cancelsTask_whenTakesTooLong() throws Exception {
        CancellableTask<Long> spinnyTask = new CancellableTask<>(executionContext, () -> {
            Random rand = new Random();
            long result = 0;
            for (long i = 0; i < Long.MAX_VALUE; i++) {
                result += rand.nextInt();
            }

            return result;
        }, Duration.ofSeconds(1));

        Optional<Long> result = spinnyTask.call();
        assertTrue(result.isEmpty());
    }
}
