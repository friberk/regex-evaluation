package dk.brics.automaton;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.junit.jupiter.api.Assertions.*;

class RegExpTest {

    @Test
    public void parsesDigits_successfully() {
        RegExp regexp = new RegExp("\\d");
        Automaton auto = regexp.toAutomaton();
        RunAutomaton runAutomaton = new RunAutomaton(auto);
        boolean matches = runAutomaton.newMatcher("1").find();
        assertThat(matches).isTrue();
    }

    @Test
    public void parsesNotDigits_successfully() {
        RegExp regexp = new RegExp("\\D");
        Automaton auto = regexp.toAutomaton();
        RunAutomaton runAutomaton = new RunAutomaton(auto);
        boolean matches = runAutomaton.newMatcher("1").find();
        assertThat(matches).isFalse();
    }

    @Test
    public void parsesWords_successfully() {
        RegExp regexp = new RegExp("\\w");
        Automaton auto = regexp.toAutomaton();
        RunAutomaton runAutomaton = new RunAutomaton(auto);
        boolean matches = runAutomaton.newMatcher("a").find();
        assertThat(matches).isTrue();
    }

    @Test
    public void parsesNotWords_successfully() {
        RegExp regexp = new RegExp("\\W");
        Automaton auto = regexp.toAutomaton();
        RunAutomaton runAutomaton = new RunAutomaton(auto);
        boolean matches = runAutomaton.newMatcher("A").find();
        assertThat(matches).isFalse();
    }

    @Test
    public void characterClassMeta_works() {
        RegExp regexp = new RegExp("[\\da]");
        Automaton auto = regexp.toAutomaton();
        RunAutomaton runAutomaton = new RunAutomaton(auto);

        boolean findsDigit = runAutomaton.newMatcher("0").find();
        boolean findsDigit2 = runAutomaton.newMatcher("8").find();
        boolean findsAlpha = runAutomaton.newMatcher("a").find();
        boolean findsBigAlpha = runAutomaton.newMatcher("A").find();
        assertThat(findsDigit).isTrue();
        assertThat(findsDigit2).isTrue();
        assertThat(findsAlpha).isTrue();
        assertThat(findsBigAlpha).isFalse();
    }

    @Test
    public void throwException_when_lowerBoundIsTooLarge() {
        assertThatThrownBy(() -> new RegExp("a{300,1000}"))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("bound 300 is too large to be compiled (must be <= 100)");
    }

    @Test
    public void throwException_when_upperBoundIsTooLarge() {
        assertThatThrownBy(() -> new RegExp("a{1,1000}"))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("bound 1000 is too large to be compiled (must be <= 100)");
    }

    @Test
    public void throwException_when_singleBoundIsTooLarge() {
        assertThatThrownBy(() -> new RegExp("a{1000}"))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("bound 1000 is too large to be compiled (must be <= 100)");
    }

    @Test
    public void failToParse_lookAheadAssertion() {
        assertThatThrownBy(() -> new RegExp("(?![a-z]+)"))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("group construct ?!");
    }

    @Test
    public void failToParse_lookAheadAssertion2() {
        assertThatThrownBy(() -> new RegExp("(?=[a-z]+)"))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("group construct ?=");
    }

    @Test
    public void failToParse_lookBehindAssertion() {
        assertThatThrownBy(() -> new RegExp("(?<![a-z]+)"))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("group construct ?<");
    }

    @Test
    public void failToParse_lookBehindAssertion2() {
        assertThatThrownBy(() -> new RegExp("(?<=[a-z]+)"))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("group construct ?<");
    }

    @Test
    public void parseRegex_andConvertToAutomaton() {
        RegExp regex = new RegExp("?(?:(a):)?(\\w{2,32}):(\\d{17,19})?");
        Automaton auto = regex.toAutomaton();
        System.out.println(auto.toDot());
    }
}