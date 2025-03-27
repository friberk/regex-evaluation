package dk.brics.automaton;

/**
 * Exception to throw if the DFA construction budget is exceeded. Basically, we can make it so that if we build too
 * many states we panic
 */
public class DfaBudgetExceededException extends RuntimeException {

    public DfaBudgetExceededException() {
        this("DFA budget exceeded");
    }

    public DfaBudgetExceededException(long stateBudget) {
        this(String.format("DFA budget of %d states exceeded", stateBudget));
    }

    public DfaBudgetExceededException(String message) {
        super(message);
    }

    public DfaBudgetExceededException(String message, Throwable cause) {
        super(message, cause);
    }
}
