package edu.institution.lab.evaluation;

import java.util.concurrent.atomic.AtomicLong;

/**
 * Record statistics about what's going on
 */
public record TestSuiteStatistics(
        AtomicLong totalTestSuites,
        AtomicLong badSyntaxPatterns,
        AtomicLong dfaBudgetExceeded
) {

    public TestSuiteStatistics() {
        this(new AtomicLong(), new AtomicLong(), new AtomicLong());
    }

    public long successfulTestSuites() {
        return totalTestSuites.get() - (badSyntaxPatterns.get() + dfaBudgetExceeded.get());
    }

    public void incrementBadSyntaxPatterns() {
        badSyntaxPatterns.incrementAndGet();
    }

    public void incrementDFABudgetExceeded() {
        dfaBudgetExceeded.incrementAndGet();
    }

    public void incrementTotalTestSuites() {
        totalTestSuites.incrementAndGet();
    }
}
