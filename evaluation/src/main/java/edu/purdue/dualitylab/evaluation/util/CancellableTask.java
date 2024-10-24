package edu.purdue.dualitylab.evaluation.util;

import java.time.Duration;
import java.util.Optional;
import java.util.concurrent.*;

/**
 * Perform a task with a timeout
 * @param <T> The task return type
 */
public class CancellableTask<T> implements Callable<Optional<T>> {

    /// where we execute the task
    private final ExecutorService executionContext;
    /// the task to execute
    private final Callable<T> task;
    /// the duration permitted for this task
    private final Duration timeout;

    /**
     * Create a new cancellable task.
     * @param executionContext The executor service that can execute this task
     * @param task The task to execute. The result from the task should be null if you want to signal a failure or
     *             if the task cannot produce a result. This implementation uses Optional#ofNullable to wrap the
     *             result.
     * @param timeout How long is permitted for this task
     */
    public CancellableTask(ExecutorService executionContext, Callable<T> task, Duration timeout) {
        this.executionContext = executionContext;
        this.task = task;
        this.timeout = timeout;
    }

    @Override
    public Optional<T> call() throws Exception {
        Future<T> futureTask = executionContext.submit(task);
        try {
            T result;
            if (this.timeout != null) {
                result = futureTask.get(timeout.getSeconds(), TimeUnit.SECONDS);
            } else {
                result = futureTask.get();
            }

            return Optional.ofNullable(result);
        } catch (TimeoutException e) {
            // if we timed out, need to cancel the task
            futureTask.cancel(true);
            return Optional.empty();
        }
    }
}
