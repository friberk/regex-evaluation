package edu.purdue.dualitylab.evaluation.stringgen;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.function.Function;
import java.util.stream.Collectors;

public final class NFA {

    public static NFA empty() {
        return new NFA();
    }

    private static Map<Integer, Integer> createStateMapping(int nextStateId, Set<Integer> originalStates) {
        Map<Integer, Integer> mapping = new HashMap<>();
        for (Integer state : originalStates) {
            mapping.put(state, state + nextStateId);
        }

        return mapping;
    }

    private static Function<Integer, Integer> createStateMappingFunction(int nextStateId) {
        return (originalState) -> originalState + nextStateId;
    }

    private static Function<Integer, Integer> createStateMappingFunction(Map<Integer, Integer> mapping) {
        return (originalState) -> mapping.getOrDefault(originalState, originalState);
    }

    private final Map<Integer, Map<Integer, Set<NFAEdge>>> automaton;
    private int acceptState;
    private int rootState;
    private int nextStateId;

    public NFA() {
        automaton = new HashMap<>();
        this.acceptState = -1;
        this.nextStateId = 0;
    }

    public int addState() {
        int stateId = this.nextStateId++;
        pushEmptyState(stateId);
        return stateId;
    }

    public int getRootState() {
        return rootState;
    }

    public int addRootState() {
        int state = addState();
        this.rootState = state;
        return state;
    }

    public int addAcceptState() {
        int state = addState();
        this.acceptState = state;
        return state;
    }

    public int getAcceptState() {
        return acceptState;
    }

    public void setAcceptState(int state) {
        this.acceptState = state;
    }

    public void addEdge(int start, int end, NFAEdge edge) {
        Map<Integer, Set<NFAEdge>> transitions = automaton.get(start);
        if (transitions == null) {
            throw new IllegalArgumentException("start state is not present in automaton");
        }

        if (transitions.containsKey(end)) {
            transitions.get(end).add(edge);
        } else {
            Set<NFAEdge> edges = new HashSet<>();
            edges.add(edge);
            transitions.put(end, edges);
        }
    }

    /**
     * Concatenate another NFA into this one, linking it into this current one
     * @param rootState The state to connect the other NFA to
     * @param other The NFA to concat
     * @param linkingEdge The edge to connect root state with other
     * @return the updated accept state
     */
    public int concatNFA(int rootState, NFA other, NFAEdge linkingEdge) {
        // re-map all of other's states
        other.remapStateIds(createStateMappingFunction(this.nextStateId));
        this.nextStateId += other.states().size();

        // now that all states are remapped, copy over the transition table
        this.automaton.putAll(other.automaton);

        // link the old NFA to the root
        this.addEdge(rootState, other.rootState, linkingEdge);

        // update the accept state
        this.acceptState = other.acceptState;

        return acceptState;
    }

    /**
     * Like concat NFA, except overlapping state on this node is treated as the root node of other
     * @param overlappingState The state that this node and other will overlap on
     * @param other Other NFA to concat
     * @return The new accept state
     */
    public int concatNFAWithOverlappingState(int overlappingState, NFA other) {
        // remap all the other states with a custom re-mapper: the root state of other turns into the overlapping state
        other.remapStateIds((otherStateId) -> {
            if (other.rootState == otherStateId) {
                return overlappingState;
            } else {
                return (otherStateId - 1) + this.nextStateId;
            }
        });
        this.nextStateId += other.states().size();
        this.acceptState = other.acceptState;
        return acceptState;
    }

    private void pushEmptyState(int stateId) {
        this.automaton.put(stateId, new HashMap<>());
    }

    private void remapStateIds(Function<Integer, Integer> mapping) {
        Map<Integer, Map<Integer, Set<NFAEdge>>> newAutomaton = new HashMap<>();
        for (var stateEntry : automaton.entrySet()) {
            int newStateId = mapping.apply(stateEntry.getKey());

            Map<Integer, Set<NFAEdge>> transitions = new HashMap<>();
            for (var transitionEntry : stateEntry.getValue().entrySet()) {
                int newDestinationId = mapping.apply(transitionEntry.getKey());
                transitions.put(newDestinationId, transitionEntry.getValue());
            }

            newAutomaton.put(newStateId, transitions);
        }

        this.acceptState = mapping.apply(this.acceptState);
        this.rootState = mapping.apply(rootState);
        this.automaton.clear();
        this.automaton.putAll(newAutomaton);
    }

    private Set<Integer> states() {
        return automaton.keySet();
    }
}
