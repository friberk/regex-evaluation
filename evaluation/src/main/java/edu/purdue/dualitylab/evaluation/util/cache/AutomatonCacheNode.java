package edu.purdue.dualitylab.evaluation.util.cache;

import dk.brics.automaton.Automaton;

/**
 * Specialized cache node for automata. We want to cache really expensive to
 * compute cache
 */
public class AutomatonCacheNode implements CacheNode<Automaton>, Comparable<AutomatonCacheNode> {

    private final long elapsedBuildTime;
    private final Automaton automaton;

    public AutomatonCacheNode(long elapsedBuildTime, Automaton automaton) {
        this.elapsedBuildTime = elapsedBuildTime;
        this.automaton = automaton;
    }

    @Override
    public Automaton getValue() {
        return automaton;
    }

    @Override
    public int compareTo(AutomatonCacheNode automatonCacheNode) {
        if (elapsedBuildTime == automatonCacheNode.elapsedBuildTime) {
            // if they have the same elapsed time, then evict the smaller one
            return Integer.compareUnsigned(this.automatonSize(), automatonCacheNode.automatonSize());
        }
        return Long.compareUnsigned(this.elapsedBuildTime, automatonCacheNode.elapsedBuildTime);
    }

    private int automatonSize() {
        return automaton.getNumberOfStates() + automaton.getNumberOfTransitions();
    }
}
