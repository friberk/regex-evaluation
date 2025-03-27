package dk.brics.automaton;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

public class TransitionTableTest {

    @Test
    void pattern1_createCorrectTable() {
        String pattern = "\\D.+";
        Automaton auto = new RegExp(pattern).toAutomaton(true);
        TransitionTable table = new TransitionTable(auto);

        assertThat(table.states()).hasSameSizeAs(auto.getStates());
        assertThat(table.countTotalTransitions()).isEqualTo(auto.getNumberOfTransitions());
    }
}
