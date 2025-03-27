package dk.brics.automaton;

import java.util.Objects;

public class Pair<T, U> {

    public static <T, U> Pair<T, U> of(T left, U right) {
        return new Pair<>(left, right);
    }

    private final T left;
    private final U right;

    public Pair(T left, U right) {
        this.left = left;
        this.right = right;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Pair<?, ?> pair = (Pair<?, ?>) o;
        return Objects.equals(left, pair.left) && Objects.equals(right, pair.right);
    }

    @Override
    public int hashCode() {
        return Objects.hash(left, right);
    }

    public T getLeft() {
        return left;
    }

    public U getRight() {
        return right;
    }
}
