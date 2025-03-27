package edu.institution.lab.evaluation.distance;

import java.util.function.BiFunction;

/**
 * Computes the distance between two things. Take in two items and produce a numerical distance
 * @param <T> The type to compute the distance from
 */
@FunctionalInterface
public interface DistanceMeasure<T> extends BiFunction<T, T, Double> {
}
