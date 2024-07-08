package edu.purdue.dualitylab.evaluation.distance;

import java.util.function.BiPredicate;
import java.util.function.Predicate;

/**
 * Given a measurement and a threshold, determine if distance between two values is acceptable
 */
public final class DistanceFilter<T> implements BiPredicate<T, T> {
    private final DistanceMeasure<T> measure;
    private final double threshold;

    public DistanceFilter(DistanceMeasure<T> measure, double threshold) {
        this.measure = measure;
        this.threshold = threshold;
    }

    @Override
    public boolean test(T left, T right) {
        double actualScore = measure.apply(left, right);
        return actualScore >= threshold;
    }
}
