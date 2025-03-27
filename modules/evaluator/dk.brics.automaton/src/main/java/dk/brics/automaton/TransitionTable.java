package dk.brics.automaton;

import java.util.*;
import java.util.function.Function;
import java.util.stream.Collectors;
import java.util.stream.Stream;

public class TransitionTable {

    private static Map<Integer, Set<Transition>> createDestTableFromState(State state) {
        Map<Integer, Set<Transition>> destinationMap = new HashMap<>();
        for (Transition trans : state.transitions) {
            int destNumber = trans.to.number;
            // Upsert the transition
            if (destinationMap.containsKey(destNumber)) {
                destinationMap.get(destNumber).add(trans);
            } else {
                Set<Transition> transitionSet = new HashSet<>();
                transitionSet.add(trans);
                destinationMap.put(destNumber, transitionSet);
            }
        }

        return destinationMap;
    }

    private static List<State> getAdjacentStates(State state) {
        Set<State> neighbors = new HashSet<>();
        for (Transition dest : state.transitions) {
            neighbors.add(dest.to);
        }

        return neighbors.stream().sorted().collect(Collectors.toList());
    }

    // Sparse matrix transition table. For each map, the key is the destination state, and the value is a set of
    // transitions that can be used to transition between the two
    private final Map<Integer, Map<Integer, Set<Transition>>> table;
    private final Set<Integer> acceptStates;
    private final int initialState;

    public TransitionTable(Automaton auto) {

        auto.determinize();

        // Initialize table
        this.table = new HashMap<>();
        this.acceptStates = new HashSet<>();

        // Populate table
        Set<State> visitedStates = new HashSet<>();
        Queue<State> traversalQueue = new ArrayDeque<>();
        traversalQueue.add(auto.getInitialState());
        while (!traversalQueue.isEmpty()) {
            State state = traversalQueue.remove();

            // skip states that have already been visited to keep traversal queue from growing unbounded-ly
            if (visitedStates.contains(state)) {
                continue;
            }

            if (state.isAccept()) {
                acceptStates.add(state.number);
            }
            visitedStates.add(state);
            // Create the entry for this state
            Map<Integer, Set<Transition>> destinationMap = createDestTableFromState(state);
            table.put(state.number, destinationMap);
            // Get the next states to check. Only enqueue states that we haven't visited yet
            getAdjacentStates(state).stream()
                    .filter(neighbor -> !visitedStates.contains(neighbor))
                    .distinct() // only visit unique adjacent states
                    .forEach(traversalQueue::add);
        }

        this.initialState = auto.getInitialState().number;
    }

    public Set<Integer> states() {
        Set<Integer> keySet = new HashSet<>(this.table.keySet());
        table.values().stream().flatMap(destMap -> destMap.keySet().stream()).forEach(keySet::add);
        return keySet;
    }

    /**
     * Count how many total transitions there are in this transition table
     * @return Transition count
     */
    public long countTotalTransitions() {
        return table.values().stream()
                .flatMap(destMap -> destMap.values().stream())
                .mapToInt(Set::size)
                .sum();
    }

    /**
     * Get the set of transitions between two states. Directed edges going from left->right
     * @param leftStateNumber Left state number (e.g. state.number)
     * @param rightStateNumber Right state number
     * @return Set of edges going from left to right
     * @throws NoSuchElementException If there are no edges between these two states
     */
    public Set<Transition> getTransitionsBetweenStates(int leftStateNumber, int rightStateNumber) {
        // Bounds checking
        if (!this.table.containsKey(leftStateNumber) || !this.table.get(leftStateNumber).containsKey(rightStateNumber)) {
            throw new NoSuchElementException("There are no edges between these two states");
        }

        return this.table.get(leftStateNumber).get(rightStateNumber);
    }

    /**
     * Step operation. Given the current state, try to step forward with the given transition character. Finds the first
     * available transition. If one is not available, then empty is returned
     * @param currentState The current state
     * @param transitionCharacter The character to take
     * @return The id of the next state, or empty if there is no suitable transition
     */
    public OptionalInt step(int currentState, char transitionCharacter) throws NoSuchElementException {
        Map<Integer, Set<Transition>> stateTransitions = Optional.ofNullable(this.table.get(currentState))
                .orElseThrow(() -> new NoSuchElementException(String.format("State %d is not in the transition table", currentState)));

        return stateTransitions.entrySet().stream()
                .filter(destinationEntry -> destinationEntry.getValue().stream()
                        .anyMatch(destinationTransition -> destinationTransition.accepts(transitionCharacter)))
                .mapToInt(Map.Entry::getKey)
                .findFirst();
    }

    /**
     * Finds any edge between states left and right that accept the given character
     * @param leftStateNumber Left state id
     * @param rightStateNumber Right state id
     * @param testChar The character to try moving across
     * @return An edge that accepts the two, otherwise empty
     * @throws NoSuchElementException if there are no edges between the two states
     */
    public Optional<Transition> findEdgeBetweenStates(int leftStateNumber, int rightStateNumber, char testChar) {
        return getTransitionsBetweenStates(leftStateNumber, rightStateNumber).stream()
                .filter(transition -> transition.accepts(testChar))
                .findAny();
    }

    public Set<AutomatonCoverage.EdgePair> possibleEdgePairs() {
        Set<AutomatonCoverage.EdgePair> edgePairs = new HashSet<>();
        for (int leftState : table.keySet()) {
            Stream<Integer> leftSuccessorStates = Stream.concat(
                    Stream.of(-1),
                    getSuccessors(leftState).stream()
            );
            Set<AutomatonCoverage.Edge> leftEdges = leftSuccessorStates
                    .flatMap(leftSuccessor -> {
                        if (leftSuccessor == -1) {
                            return Stream.of(AutomatonCoverage.Edge.failEdge(leftState));
                        }

                        return getTransitionsBetweenStates(leftState, leftSuccessor).stream()
                                .map(transition -> new AutomatonCoverage.Edge(leftState, leftSuccessor, transition));
                    })
                    .collect(Collectors.toSet());

            for (AutomatonCoverage.Edge leftEdge : leftEdges) {
                int middleState = leftEdge.getRightStateId();
                Stream<Integer> middleSuccessorStates = Stream.concat(
                        Stream.of(-1),
                        getSuccessors(middleState).stream()
                );

                middleSuccessorStates
                        .flatMap(middleSuccessor -> {
                            if (middleSuccessor == -1) {
                                return Stream.of(AutomatonCoverage.Edge.failEdge(middleState));
                            }

                            return getTransitionsBetweenStates(middleState, middleSuccessor).stream()
                                    .map(transition -> new AutomatonCoverage.Edge(middleState, middleSuccessor, transition));
                        })
                        .forEach(destEdge -> edgePairs.add(new AutomatonCoverage.EdgePair(leftEdge, destEdge)));
            }
        }

        return edgePairs;
    }

    public int getInitialState() {
        return initialState;
    }

    public String toDot() {

        Function<Character, String> printableCharacter = (ch) -> {
            if (Character.isAlphabetic(ch) || Character.isDigit(ch)) {
                return String.valueOf(ch);
            } else {
                return String.format("\\u%04x", (int) ch);
            }
        };

        StringBuilder builder = new StringBuilder();
        builder.append("digraph automaton {\n");
        builder.append("\trankdir = LR;\n");
        for (int state : this.table.keySet()) {
            String shape = acceptStates.contains(state) ? "doublecircle" : "circle";
            builder.append(String.format("\t%d [shape=%s, label=%d]\n", state, shape, state));
        }

        for (Map.Entry<Integer, Map<Integer, Set<Transition>>> entry : table.entrySet()) {
            int originState = entry.getKey();
            Map<Integer, Set<Transition>> destMap = entry.getValue();
            for (Map.Entry<Integer, Set<Transition>> destEntry : destMap.entrySet()) {
                int dest = destEntry.getKey();
                Set<Transition> transitions = destEntry.getValue();

                for (Transition trans : transitions) {
                    String label;
                    if (trans.getMin() == trans.getMax()) {
                        label = printableCharacter.apply(trans.getMin());
                    } else {
                        String lowerPrintableBound = printableCharacter.apply(trans.getMin());
                        String upperPrintableBound = printableCharacter.apply(trans.getMax());
                        label = String.format("[%s,%s]", lowerPrintableBound, upperPrintableBound);
                    }
                    builder.append(String.format("\t%d -> %d [label=\"%s\"]\n", originState, dest, label));
                }
            }
        }

        builder.append("}\n");
        return builder.toString();
    }

    private Set<Integer> getSuccessors(int state) {
        Map<Integer, Set<Transition>> outgoingTransitions = this.table.get(state);
        if (outgoingTransitions == null) {
            return Collections.emptySet();
        }

        return outgoingTransitions.keySet();
    }
}
