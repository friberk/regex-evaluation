package dk.brics.automaton;

import java.util.*;

public class AutomatonCoverage {

    public static final int FAILURE_STATE_ID = -1;

    public static final class Edge {

        public static Edge failEdge(int originState) {
            return new Edge(originState, FAILURE_STATE_ID, (char) 0, (char) 0, -1);
        }

        private final int leftStateId;
        private final int rightStateId;
        private final char edgeMin;
        private final char edgeMax;
        private final int transId;

        public Edge(int leftStateId, int rightStateId, Transition transition) {
            this(leftStateId, rightStateId, transition.getMin(), transition.getMax(), transition.getId());
        }

        public Edge(int leftStateId, int rightStateId, char edgeMin, char edgeMax, int transId) {
            this.leftStateId = leftStateId;
            this.rightStateId = rightStateId;
            this.edgeMin = edgeMin;
            this.edgeMax = edgeMax;
            this.transId = transId;
        }

        @Override
        public boolean equals(Object o) {
            if (this == o) return true;
            if (o == null || getClass() != o.getClass()) return false;
            Edge edge = (Edge) o;
            return leftStateId == edge.leftStateId && rightStateId == edge.rightStateId && edgeMin == edge.edgeMin && edgeMax == edge.edgeMax;
        }

        @Override
        public int hashCode() {
            return Objects.hash(leftStateId, rightStateId, edgeMin, edgeMax);
        }

        @Override
        public String toString() {
            return "Edge{" +
                    "leftStateId=" + leftStateId +
                    ", rightStateId=" + rightStateId +
                    ", transId=" + transId +
                    ", edgeMin=" + edgeMin +
                    ", edgeMax=" + edgeMax +
                    '}';
        }

        public int getLeftStateId() {
            return leftStateId;
        }

        public int getRightStateId() {
            return rightStateId;
        }
    }

    public static final class EdgePair {
        private final Edge leftEdge;
        private final Edge rightEdge;

        public EdgePair(Edge leftEdge, Edge rightEdge) {
            this.leftEdge = leftEdge;
            this.rightEdge = rightEdge;
        }

        @Override
        public boolean equals(Object o) {
            if (this == o) return true;
            if (o == null || getClass() != o.getClass()) return false;
            EdgePair edgePair = (EdgePair) o;
            return Objects.equals(leftEdge, edgePair.leftEdge) && Objects.equals(rightEdge, edgePair.rightEdge);
        }

        @Override
        public int hashCode() {
            return Objects.hash(leftEdge, rightEdge);
        }

        @Override
        public String toString() {
            return "EdgePair{" +
                    "leftEdge=" + leftEdge +
                    ", rightEdge=" + rightEdge +
                    '}';
        }
    }

    public static final class VisitationInfo {
        private final Set<Integer> visitedNodes;
        private final Map<Edge, Set<Character>> visitedEdges;
        private final Set<EdgePair> visitedEdgePairs;

        public VisitationInfo() {
            this(new HashSet<>(), new HashMap<>(), new HashSet<>());
        }

        public VisitationInfo(Set<Integer> visitedNodes, Map<Edge, Set<Character>> visitedEdges, Set<EdgePair> visitedEdgePairs) {
            this.visitedNodes = visitedNodes;
            this.visitedEdges = visitedEdges;
            this.visitedEdgePairs = visitedEdgePairs;
        }

        public Set<Integer> getVisitedNodes() {
            return visitedNodes;
        }

        public Map<Edge, Set<Character>> getVisitedEdges() {
            return visitedEdges;
        }

        public Set<EdgePair> getVisitedEdgePairs() {
            return visitedEdgePairs;
        }

        private void addVisitedNode(int node) {
            visitedNodes.add(node);
        }

        public void addVisitedEdge(Edge edge, char ch) {
            visitedEdges.putIfAbsent(edge, new HashSet<>());
            visitedEdges.get(edge).add(ch);
        }

        public void addVisitedEdgePair(EdgePair edgePair) {
            visitedEdgePairs.add(edgePair);
        }

        public void foldIn(VisitationInfo other) {
            this.visitedNodes.addAll(other.getVisitedNodes());
            other.getVisitedEdges().forEach((key, value) -> this.visitedEdges.merge(key, value, (existing, incoming) -> {
                existing.addAll(incoming);
                return existing;
            }));
            this.visitedEdgePairs.addAll(other.getVisitedEdgePairs());
        }

        @Override
        public boolean equals(Object o) {
            if (this == o) return true;
            if (o == null || getClass() != o.getClass()) return false;
            VisitationInfo that = (VisitationInfo) o;
            return Objects.equals(visitedNodes, that.visitedNodes) && Objects.equals(visitedEdges, that.visitedEdges) && Objects.equals(visitedEdgePairs, that.visitedEdgePairs);
        }

        @Override
        public int hashCode() {
            return Objects.hash(visitedNodes, visitedEdges, visitedEdgePairs);
        }
    }

    public static final class VisitationInfoSummary {
        private final double nodeCoverage;
        private final double edgeCoverage;
        private final double edgePairCoverage;

        public VisitationInfoSummary(double nodeCoverage, double edgeCoverage, double edgePairCoverage) {
            this.nodeCoverage = nodeCoverage;
            this.edgeCoverage = edgeCoverage;
            this.edgePairCoverage = edgePairCoverage;
        }

        @Override
        public boolean equals(Object o) {
            if (this == o) return true;
            if (o == null || getClass() != o.getClass()) return false;
            VisitationInfoSummary that = (VisitationInfoSummary) o;
            return Double.compare(nodeCoverage, that.nodeCoverage) == 0 && Double.compare(edgeCoverage, that.edgeCoverage) == 0 && Double.compare(edgePairCoverage, that.edgePairCoverage) == 0;
        }

        @Override
        public int hashCode() {
            return Objects.hash(nodeCoverage, edgeCoverage, edgePairCoverage);
        }

        public double getNodeCoverage() {
            return nodeCoverage;
        }

        public double getEdgeCoverage() {
            return edgeCoverage;
        }

        public double getEdgePairCoverage() {
            return edgePairCoverage;
        }
    }

    private static double edgeCoverageAmount(Edge edge, Set<Character> coveredChars) {
        // edges to error states always get complete covered. We are less interested in how covered these are
        // than if they are covered at all
        if (edge.leftStateId == FAILURE_STATE_ID || edge.rightStateId == FAILURE_STATE_ID) {
            return 1;
        }

        int totalCharacters = edge.edgeMax - edge.edgeMin + 1;
        return ((double) coveredChars.size()) / totalCharacters;
    }

    private final Automaton originalAutomaton;
    private final TransitionTable transitionTable;

    private final VisitationInfo fullMatchVisitationInfo;
    private final VisitationInfo partialMatchVisitationInfo;

    public AutomatonCoverage(Automaton automaton) {
        this.originalAutomaton = automaton;
        this.transitionTable = new TransitionTable(automaton);

        fullMatchVisitationInfo = new VisitationInfo();
        partialMatchVisitationInfo = new VisitationInfo();
    }

    protected AutomatonCoverage(Automaton automaton, TransitionTable transitionTable) {
        this.originalAutomaton = automaton;
        this.transitionTable = transitionTable;

        fullMatchVisitationInfo = new VisitationInfo();
        partialMatchVisitationInfo = new VisitationInfo();
    }

    public void evaluate(String subject) {
        fullMatchVisitationInfo.foldIn(evaluateString(subject, true));
        partialMatchVisitationInfo.foldIn(evaluateString(subject, false));
    }

    public VisitationInfoSummary getFullMatchVisitationInfoSummary() {
        return summarizeVisitationInfo(getFullMatchVisitationInfo());
    }

    public VisitationInfoSummary getPartialMatchVisitationInfoSummary() {
        return summarizeVisitationInfo(getPartialMatchVisitationInfo());
    }

    private VisitationInfoSummary summarizeVisitationInfo(VisitationInfo info) {
        double nodeCoverage = (double) info.getVisitedNodes().size() / computeNumberOfStates();
        double allEdgeCoverageAmount = info.getVisitedEdges().entrySet().stream()
                .mapToDouble(entry -> edgeCoverageAmount(entry.getKey(), entry.getValue()))
                .sum();
        double edgeCoverage = allEdgeCoverageAmount / computeNumberOfEdges();
        double edgePairCoverage = (double) info.getVisitedEdgePairs().size() / computeNumberOfEdgePairs();

        return new VisitationInfoSummary(nodeCoverage, edgeCoverage, edgePairCoverage);
    }

    public VisitationInfo getFullMatchVisitationInfo() {
        return fullMatchVisitationInfo;
    }

    public VisitationInfo getPartialMatchVisitationInfo() {
        return partialMatchVisitationInfo;
    }

    private VisitationInfo evaluateString(String input, boolean fullMatch) {
        VisitationInfo visitationInfo = new VisitationInfo();
        Optional<Edge> previousEdge = Optional.empty();
        int stateCursor = transitionTable.getInitialState();
        visitationInfo.addVisitedNode(stateCursor);

        int currentPos = 0;
        while (currentPos < input.length()) {
            char transitionCharacter = input.charAt(currentPos);

            OptionalInt nextStateOpt = this.transitionTable.step(stateCursor, transitionCharacter);
            if (nextStateOpt.isEmpty()) {

                // add visited node
                visitationInfo.addVisitedNode(FAILURE_STATE_ID);

                // we have encountered a failure state/edge
                Edge failEdge = Edge.failEdge(stateCursor);
                visitationInfo.addVisitedEdge(failEdge, transitionCharacter);

                // add an edge pair as well
                previousEdge.ifPresent(prevEdge -> visitationInfo.addVisitedEdgePair(new EdgePair(prevEdge, failEdge)));

                // there's no outgoing state, then there are two things we can try:
                if (fullMatch) {

                    // if there is any remaining input, then we should add an edge for the covered self loop
                    if (currentPos + 1 < input.length()) {
                        Edge failSelfLoop = Edge.failEdge(FAILURE_STATE_ID);
                        visitationInfo.addVisitedEdge(failSelfLoop, transitionCharacter);
                        visitationInfo.addVisitedEdgePair(new EdgePair(failEdge, failSelfLoop));
                    }

                    // if we're in full match mode, then we're done
                    break;
                } else {
                    // otherwise, we should restart the automaton
                    stateCursor = transitionTable.getInitialState();
                    previousEdge = Optional.empty();
                }
            } else {
                int nextState = nextStateOpt.getAsInt();
                Transition joiningTransition = findTransitionForState(stateCursor, nextState, transitionCharacter).orElseThrow();
                // We moved to another state, so that state should be marked as visited
                visitationInfo.addVisitedNode(nextState);

                // construct an edge with our current state info
                Edge takenEdge = new Edge(stateCursor, nextState, joiningTransition);
                visitationInfo.addVisitedEdge(takenEdge, transitionCharacter);

                // record edge pair if possible
                previousEdge.ifPresent(prevEdge -> visitationInfo.addVisitedEdgePair(new EdgePair(prevEdge, takenEdge)));

                // move states along
                previousEdge = Optional.of(takenEdge);
                stateCursor = nextState;
            }
            // Update the cursor
            currentPos++;
        }

        return visitationInfo;
    }

    private int computeNumberOfStates() {
        // add one for the error state
        return originalAutomaton.getLiveStates().size() // all states already in the automaton
                + 1; // plus the error state
    }

    private int computeNumberOfEdges() {
        // all edges + an edge from each state to the failure state
        return originalAutomaton.getNumberOfTransitions() // all edges from normal node to normal node
                + originalAutomaton.getNumberOfStates() // + an edge from each node to the fail state
                + 1; // plus an edge from the fail state to the fail state
    }

    /**
     * TODO figure out how to compute this without using the transition table
     * @return Number of possible edge pairs
     */
    private int computeNumberOfEdgePairs() {
        return transitionTable.possibleEdgePairs().size();
    }

    Set<EdgePair> missingFullMatchEdgePairs() {
        Set<EdgePair> possibleEdges = transitionTable.possibleEdgePairs();
        possibleEdges.removeAll(fullMatchVisitationInfo.getVisitedEdgePairs());
        return possibleEdges;
    }

    protected TransitionTable getTransitionTable() {
        return transitionTable;
    }

    /**
     * Find a transition between the two given states that accepts the given transition character
     * @param startState left state
     * @param endState destination state
     * @param transitionChar The character
     * @return Transition between the two with the given character, or empty if doesn't exist
     */
    private Optional<Transition> findTransitionForState(int startState, int endState, char transitionChar) {
        try {
            return transitionTable.getTransitionsBetweenStates(startState, endState).stream()
                    .filter(transition -> transition.getMin() <= transitionChar && transitionChar <= transition.getMax())
                    .findFirst();
        } catch (NoSuchElementException notFound) {
            return Optional.empty();
        }
    }
}
