package edu.purdue.dualitylab.evaluation.distance;

import dk.brics.automaton.Automaton;
import dk.brics.automaton.RegExp;

final class DistanceUtils {

    /**
     * Take an automaton distance measure and wrap it into a string distance measure that converts the parameters into
     * automata and then applies the measure
     * @param autoMeasure The automaton distance measure to use
     * @return A string distance measure that converts the args
     */
    public static DistanceMeasure<String> createStringDistanceMeasure(DistanceMeasure<Automaton> autoMeasure) {
        return (left, right) -> {
            Automaton leftAuto = new RegExp(left).toAutomaton(true);
            Automaton rightAuto = new RegExp(right).toAutomaton(true);

            return autoMeasure.apply(leftAuto, rightAuto);
        };
    }
}
