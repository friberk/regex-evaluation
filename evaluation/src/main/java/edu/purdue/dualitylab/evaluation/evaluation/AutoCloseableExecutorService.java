package edu.purdue.dualitylab.evaluation.evaluation;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Duration;
import java.util.Collection;
import java.util.List;
import java.util.concurrent.*;

/**
 * Basic executor service that uses the AutoClosable interface for automatically shutting down
 * the wrapped executor service. The shutdown policy is to try to gracefully shutdown. If graceful
 * shutdown fails, force shutdown.
 */
public class AutoCloseableExecutorService implements ExecutorService, AutoCloseable {


    private static final Logger logger = LoggerFactory.getLogger(AutoCloseableExecutorService.class);
    private final ExecutorService innerExecutor;
    private final Duration waitDuration;

    public AutoCloseableExecutorService(ExecutorService innerExecutor) {
        this(innerExecutor, Duration.ofSeconds(10));
    }

    public AutoCloseableExecutorService(ExecutorService innerExecutor, Duration waitDuration) {
        this.innerExecutor = innerExecutor;
        this.waitDuration = waitDuration;
    }

    @Override
    public void shutdown() {
        innerExecutor.shutdown();
    }

    @Override
    public List<Runnable> shutdownNow() {
        return innerExecutor.shutdownNow();
    }

    @Override
    public boolean isShutdown() {
        return innerExecutor.isShutdown();
    }

    @Override
    public boolean isTerminated() {
        return innerExecutor.isTerminated();
    }

    @Override
    public boolean awaitTermination(long l, TimeUnit timeUnit) throws InterruptedException {
        return innerExecutor.awaitTermination(l, timeUnit);
    }

    @Override
    public <T> Future<T> submit(Callable<T> callable) {
        return innerExecutor.submit(callable);
    }

    @Override
    public <T> Future<T> submit(Runnable runnable, T t) {
        return innerExecutor.submit(runnable, t);
    }

    @Override
    public Future<?> submit(Runnable runnable) {
        return innerExecutor.submit(runnable);
    }

    @Override
    public <T> List<Future<T>> invokeAll(Collection<? extends Callable<T>> collection) throws InterruptedException {
        return innerExecutor.invokeAll(collection);
    }

    @Override
    public <T> List<Future<T>> invokeAll(Collection<? extends Callable<T>> collection, long l, TimeUnit timeUnit) throws InterruptedException {
        return innerExecutor.invokeAll(collection, l, timeUnit);
    }

    @Override
    public <T> T invokeAny(Collection<? extends Callable<T>> collection) throws InterruptedException, ExecutionException {
        return innerExecutor.invokeAny(collection);
    }

    @Override
    public <T> T invokeAny(Collection<? extends Callable<T>> collection, long l, TimeUnit timeUnit) throws InterruptedException, ExecutionException, TimeoutException {
        return innerExecutor.invokeAny(collection, l, timeUnit);
    }

    @Override
    public void close() {
        try {
            innerExecutor.shutdown();
            boolean done = innerExecutor.awaitTermination(waitDuration.toSeconds(), TimeUnit.SECONDS);
            if (!done) {
                innerExecutor.shutdownNow();
            }
        } catch (InterruptedException e) {
            throw new RuntimeException(e);
        }
    }

    @Override
    public void execute(Runnable runnable) {
        innerExecutor.execute(runnable);
    }
}
