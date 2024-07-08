package edu.purdue.dualitylab.evaluation.distance;

import dk.brics.automaton.Automaton;

/**
 * Computes the size of the "overhang," or |(union - intersection)| / |union|
 */
public final class OverhangSizeDistance implements DistanceMeasure<Automaton> {
    @Override
    public Double apply(Automaton left, Automaton right) {
        Automaton intersection = AutomatonUtils.shrinkAutomaton(left.intersection(right));
        Automaton union = AutomatonUtils.shrinkAutomaton(left.union(right));
        Automaton overhang = AutomatonUtils.shrinkAutomaton(union.minus(intersection));

        double overhangSize = AutomatonUtils.automatonSize(overhang) / AutomatonUtils.automatonSize(union);
        return 1 - overhangSize;
    }
}
