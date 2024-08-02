package edu.purdue.dualitylab.evaluation.util;

public record Pair<A, B>(
        A left,
        B right
) {
    public static <A, B> Pair<A, B> of(A a, B b) {
        return new Pair<>(a, b);
    }
}
