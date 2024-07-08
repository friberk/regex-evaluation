package edu.purdue.dualitylab.evaluation.distance;

import dk.brics.automaton.Automaton;

/**
 * Compute the intersection over union between two automata
 */
public final class IntersectionOverUnionDistance implements DistanceMeasure<Automaton> {
    @Override
    public Double apply(Automaton left, Automaton right) {
        Automaton intersection = AutomatonUtils.shrinkAutomaton(left.intersection(right));
        Automaton union = AutomatonUtils.shrinkAutomaton(left.union(right));

        return AutomatonUtils.automatonSize(intersection) / AutomatonUtils.automatonSize(union);
    }
}
