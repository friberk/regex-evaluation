package edu.purdue.dualitylab.evaluation.stringgen;

import java.util.Objects;

public final class QuantifierInfo {

    public static QuantifierInfo questionMark() {
        return new QuantifierInfo(0, 1);
    }

    public static QuantifierInfo star() {
        return new QuantifierInfo(0, Double.POSITIVE_INFINITY);
    }

    public static QuantifierInfo plus() {
        return new QuantifierInfo(1, Double.POSITIVE_INFINITY);
    }

    public static QuantifierInfo atLeast(int lower) {
        return new QuantifierInfo(lower, Double.POSITIVE_INFINITY);
    }

    public static QuantifierInfo exactly(int count) {
        return new QuantifierInfo(count, count);
    }

    public static QuantifierInfo bounded(int lower, int upper) {
        return new QuantifierInfo(lower, upper);
    }

    private final int min;
    private final double max;

    private QuantifierInfo(int min, double max) {
        if (min > max) {
            throw new IllegalArgumentException("Min must be less than or equal to max");
        }
        this.min = min;
        this.max = max;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        QuantifierInfo that = (QuantifierInfo) o;
        return min == that.min && Double.compare(max, that.max) == 0;
    }

    @Override
    public int hashCode() {
        return Objects.hash(min, max);
    }

    public int getMin() {
        return min;
    }

    public double getMax() {
        return max;
    }

    public boolean isInfiniteUpperBound() {
        return max == Double.POSITIVE_INFINITY;
    }
}
