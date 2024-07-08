package edu.purdue.dualitylab.evaluation.distance;

import dk.brics.automaton.Automaton;

class AutomatonUtils {
    public static double automatonSize(Automaton automaton) {
        return automaton.getNumberOfTransitions();
    }

    public static Automaton shrinkAutomaton(Automaton automaton) {
        automaton.determinize();
        automaton.minimize();
        return automaton;
    }
}
