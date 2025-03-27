package dk.brics.automaton;

import org.junit.jupiter.api.Test;

import java.util.Collection;

import static org.assertj.core.api.Assertions.assertThat;

public class GenerateStringsTest {

    @Test
    void shouldGenerateStrings_for_regex() {
        String pattern = "^(?:(@[^/]+)\\/)?([^/]+)$";
        RegExp regex = new RegExp(pattern);
        Automaton patternAuto = regex.toAutomaton();
        System.out.println(patternAuto.toDot());
        Collection<String> trueStrings = GenerateStrings.generateStrings(pattern, new GenerateStrings.GenerateStringsConfiguration(true, 2, 10));
        for (String str : trueStrings) {
            System.out.println(str);
        }
        assertThat(trueStrings).isNotEmpty();
    }

    @Test
    void gen() {
        String pattern = "^(?:(?:plugin:(?:(@[^/]+)\\/)?([^@]{1}[^/]*)\\/)|bpmnlint:)([^/]+)$";
        RegExp regex = new RegExp(pattern);
        Automaton patternAuto = regex.toAutomaton();
        System.out.println(patternAuto.toDot());
        Collection<String> trueStrings = GenerateStrings.generateStrings(pattern, new GenerateStrings.GenerateStringsConfiguration(true, 2, 10));
        for (String str : trueStrings) {
            System.out.println(str);
        }
        assertThat(trueStrings).isNotEmpty();
    }
}
