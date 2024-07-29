package edu.purdue.dualitylab.evaluation.stringgen;

public final class NFAEdge {

    public enum QuantifierEnd {
        START,
        END,
        SINGLE
    }

    public static NFAEdge epsilon() {
        return new NFAEdge(QuantifierInfo.exactly(1), QuantifierEnd.SINGLE);
    }

    private final char lower;
    private final char upper;
    private final QuantifierInfo quantifierInfo;
    private final QuantifierEnd quantifierEnd;

    public NFAEdge(QuantifierInfo quantifierInfo, QuantifierEnd end) {
        this((char) 0, quantifierInfo, end);
    }

    public NFAEdge(char single, QuantifierInfo quantifierInfo, QuantifierEnd end) {
        this(single, single, quantifierInfo, end);
    }

    public NFAEdge(char lower, char upper, QuantifierInfo quantifierInfo, QuantifierEnd end) {
        if (lower > upper) {
            throw new IllegalArgumentException("lower must be less than upper");
        }
        this.lower = lower;
        this.upper = upper;
        this.quantifierInfo = quantifierInfo;
        this.quantifierEnd = end;
    }
}
