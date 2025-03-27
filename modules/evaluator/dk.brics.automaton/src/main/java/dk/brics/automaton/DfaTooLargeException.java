package dk.brics.automaton;

public class DfaTooLargeException extends Exception {
    public DfaTooLargeException(Automaton automaton) {
        super(String.format("DFA is too large with %d states and %d transitions", automaton.getNumberOfStates(), automaton.getNumberOfTransitions()));
    }
}
