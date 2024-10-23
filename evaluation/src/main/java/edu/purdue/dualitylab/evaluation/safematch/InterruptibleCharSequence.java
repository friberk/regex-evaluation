package edu.purdue.dualitylab.evaluation.safematch;

/**
 * Allows us to interrupt a thread while evaluating a regex on the given character sequence.
 */
class InterruptibleCharSequence implements CharSequence {
    CharSequence inner;
    // public long counter = 0;

    public InterruptibleCharSequence(CharSequence inner) {
        super();
        this.inner = inner;
    }

    public char charAt(int index) {
        if (Thread.interrupted()) { // clears flag if set
            throw new RuntimeException(new InterruptedException());
        }
        // counter++;
        return inner.charAt(index);
    }

    public int length() {
        return inner.length();
    }

    public CharSequence subSequence(int start, int end) {
        return new InterruptibleCharSequence(inner.subSequence(start, end));
    }

    @Override
    public String toString() {
        return inner.toString();
    }
}
