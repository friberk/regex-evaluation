package dk.brics.automaton;

import org.junit.jupiter.api.Test;

import java.util.Collection;
import java.util.Set;
import java.util.function.Consumer;
import java.util.stream.Collectors;
import java.util.stream.IntStream;

import static org.assertj.core.api.Assertions.assertThat;

class AutomatonCoverageTest {

    @Test
    void pattern1_coverage_shouldHaveFullCoverage() throws DfaTooLargeException {
        Automaton auto = prepareRegex("(a|b)");
        AutomatonCoverage coverage = new AutomatonCoverage(auto);

        System.out.println(coverage.getTransitionTable().toDot());

        coverage.evaluate("a");
        coverage.evaluate("b");
        coverage.evaluate("c");
        coverage.evaluate("aa");
        coverage.evaluate("aaa");
        assertFullMatchCoverage(
                coverage,
                info -> {
                    assertThat(info.getVisitedNodes()).containsExactlyInAnyOrder(-1, 0, 1);
                },
                summary -> {
                    assertThat(summary.getNodeCoverage()).isEqualTo(1.0);
                    assertThat(summary.getEdgeCoverage()).isEqualTo(1.0);
                }
        );
    }

    @Test
    void pattern2_coverage_shouldHaveFullCoverage() throws DfaTooLargeException {
        Automaton auto = prepareRegex("a(b|c)d");
        System.out.println(auto.toDot());
        AutomatonCoverage coverage = new AutomatonCoverage(auto);

        coverage.evaluate("abd");
        assertFullMatchCoverage(
                coverage,
                info -> {
                    assertThat(info.getVisitedNodes()).containsExactlyInAnyOrderElementsOf(statesToStateNums(auto.getLiveStates()));
                    assertThat(info.getVisitedEdges().size()).isEqualTo(auto.getNumberOfTransitions());
                },
                summary -> {
                    assertThat(summary.getNodeCoverage()).isLessThan(1.0);
                    assertThat(summary.getEdgeCoverage()).isLessThan(1.0);
                }
        );

        coverage.evaluate("b");
        coverage.evaluate("ae");
        coverage.evaluate("abe");
        coverage.evaluate("acd");
        coverage.evaluate("abde");
        coverage.evaluate("abdee");
        assertFullMatchCoverage(
                coverage,
                info -> {},
                summary -> {
                    assertThat(summary.getNodeCoverage()).isEqualTo(1.0);
                    assertThat(summary.getEdgeCoverage()).isEqualTo(1.0);
                }
        );
    }

    @Test
    void pattern3_coverage_hasIncompleteNodeCoverage() throws DfaTooLargeException {
        Automaton auto = prepareRegex("^http(s)?:\\/\\/$");
        System.out.println(auto.toDot());
        AutomatonCoverage coverage = new AutomatonCoverage(auto);
        System.out.println(coverage.getTransitionTable().toDot());

        coverage.evaluate("http://");

        assertFullMatchCoverage(
                coverage,
                info -> {
                },
                summary -> assertThat(summary.getNodeCoverage()).isEqualTo(8 / 10.0)
        );
    }

    @Test
    void pattern3_coverage_hasIncompleteEdgeCoverage() throws DfaTooLargeException {
        Automaton auto = prepareRegex("^http(s)?:\\/\\/$");
        System.out.println(auto.toDot());
        AutomatonCoverage coverage = new AutomatonCoverage(auto);

        coverage.evaluate("https://");

        AutomatonCoverage.VisitationInfo info = coverage.getFullMatchVisitationInfo();

        Set<Integer> states = statesToStateNums(auto.getLiveStates());
        assertThat(info.getVisitedNodes()).containsExactlyInAnyOrderElementsOf(states);
        assertThat(info.getVisitedEdges().size()).isEqualTo(auto.getNumberOfTransitions() - 1);
    }

    @Test
    void pattern3_coverage_hasCompleteCoverage() throws DfaTooLargeException {
        Automaton auto = prepareRegex("^http(s)?:\\/\\/$");
        System.out.println(auto.toDot());
        AutomatonCoverage coverage = new AutomatonCoverage(auto);

        coverage.evaluate("https://");
        coverage.evaluate("http://");

        AutomatonCoverage.VisitationInfo info = coverage.getFullMatchVisitationInfo();

        assertThat(info.getVisitedNodes()).containsExactlyInAnyOrderElementsOf(statesToStateNums(auto.getLiveStates()));
        assertThat(info.getVisitedEdges().size()).isEqualTo(auto.getNumberOfTransitions());
    }

    @Test
    void pattern4_coverage_hasCompleteCoverage() throws DfaTooLargeException {
        Automaton auto = prepareRegex("[a-z0-9]*A");
        System.out.println(auto.toDot());
        AutomatonCoverage coverage = new AutomatonCoverage(auto);

        coverage.evaluate("A");
        assertFullMatchCoverage(
                coverage,
                info -> {
                    assertThat(info.getVisitedNodes()).containsExactly(0, 1);
                },
                summary -> {
                    assertThat(summary.getNodeCoverage()).isLessThan(1.0);
                    assertThat(summary.getEdgeCoverage()).isEqualTo(1.0 / 6.0);
                }
        );

        coverage.evaluate("*");
        assertFullMatchCoverage(
                coverage,
                info -> {
                    assertThat(info.getVisitedNodes()).containsExactlyInAnyOrder(0, 1, -1);
                },
                summary -> {
                    assertThat(summary.getNodeCoverage()).isEqualTo(1.0);
                    assertThat(summary.getEdgeCoverage()).isEqualTo(2.0 / 6.0);
                }
        );

        coverage.evaluate("Ab");
        assertFullMatchCoverage(
                coverage,
                info -> {
                    assertThat(info.getVisitedNodes()).containsExactlyInAnyOrder(0, 1, -1);
                },
                summary -> {
                    assertThat(summary.getNodeCoverage()).isEqualTo(1.0);
                    assertThat(summary.getEdgeCoverage()).isEqualTo(3.0 / 6.0);
                }
        );

        IntStream.rangeClosed('a', 'z')
                                .mapToObj(cval -> (char) cval)
                                .map(ch -> String.format("%cA", ch))
                                .forEach(coverage::evaluate);
        assertFullMatchCoverage(
                coverage,
                info -> {
                    assertThat(info.getVisitedNodes()).containsExactlyInAnyOrder(0, 1, -1);
                },
                summary -> {
                    assertThat(summary.getNodeCoverage()).isEqualTo(1.0);
                    assertThat(summary.getEdgeCoverage()).isEqualTo(4.0 / 6.0);
                }
        );

        IntStream.rangeClosed('0', '9')
                .mapToObj(cval -> (char) cval)
                .map(ch -> String.format("%cA", ch))
                .forEach(coverage::evaluate);
        assertFullMatchCoverage(
                coverage,
                info -> {
                    assertThat(info.getVisitedNodes()).containsExactlyInAnyOrder(0, 1, -1);
                },
                summary -> {
                    assertThat(summary.getNodeCoverage()).isEqualTo(1.0);
                    assertThat(summary.getEdgeCoverage()).isEqualTo(5.0 / 6.0);
                }
        );


        coverage.evaluate("0AAA");
        assertFullMatchCoverage(
                coverage,
                info -> {
                    assertThat(info.getVisitedNodes()).containsExactlyInAnyOrder(0, 1, -1);
                },
                summary -> {
                    assertThat(summary.getNodeCoverage()).isEqualTo(1.0);
                    assertThat(summary.getEdgeCoverage()).isEqualTo(1.0);
                }
        );
    }

    // @Test
    void pattern6_coverage_hasFullCoverage() {
        Automaton auto = prepareRegex("\\d*([A-Z\\s]|[bc])+e");
        // TransitionTable transitionTable = new TransitionTable(auto);
        // System.out.println(transitionTable.toDot());
        AutomatonCoverage coverage = new AutomatonCoverage(auto);

        coverage.evaluate("0Ae");
        assertFullMatchCoverage(
                coverage,
                info -> {
                    assertThat(info.getVisitedNodes()).containsExactlyInAnyOrder(0, 1, 2);
                },
                summary -> {
                    assertThat(summary.getNodeCoverage()).isLessThan(1.0);
                    assertThat(summary.getEdgeCoverage()).isEqualTo(3 / 14.0);
                    assertThat(summary.getEdgePairCoverage()).isEqualTo(2.0 / 58.0);
                }
        );

        coverage.evaluate("be");
        coverage.evaluate("Ze");
        coverage.evaluate("\te");
        coverage.evaluate("\u000ce");

        assertFullMatchCoverage(
                coverage,
                info -> {
                    assertThat(info.getVisitedNodes()).containsExactlyInAnyOrder(0, 1, 2);
                },
                summary -> {
                    assertThat(summary.getNodeCoverage()).isLessThan(1.0);
                    assertThat(summary.getEdgeCoverage()).isEqualTo(6 / 14.0);
                    assertThat(summary.getEdgePairCoverage()).isEqualTo(5.0 / 58.0);
                }
        );

        coverage.evaluate("bbe");
        coverage.evaluate("ZAe");
        coverage.evaluate("\t\te");
        coverage.evaluate("\u000c\u000ce");

        assertFullMatchCoverage(
                coverage,
                info -> {
                    assertThat(info.getVisitedNodes()).containsExactlyInAnyOrder(0, 1, 2);
                },
                summary -> {
                    assertThat(summary.getNodeCoverage()).isLessThan(1.0);
                    assertThat(summary.getEdgeCoverage()).isEqualTo(10 / 14.0);
                    assertThat(summary.getEdgePairCoverage()).isEqualTo(13.0 / 58.0);
                }
        );

        coverage.evaluate("a");
        coverage.evaluate("Aa");
        coverage.evaluate("AeA");
        coverage.evaluate("AeAA");

        assertFullMatchCoverage(
                coverage,
                info -> {
                    assertThat(info.getVisitedNodes()).containsExactlyInAnyOrder(-1, 0, 1, 2);
                },
                summary -> {
                    assertThat(summary.getNodeCoverage()).isEqualTo(1.0);
                    assertThat(summary.getEdgeCoverage()).isEqualTo(1.0);
                    assertThat(summary.getEdgePairCoverage()).isEqualTo(16.0 / 58.0);
                }
        );

        coverageEvaluateAllIterable(coverage, Set.of(
                "0a",
                // one repetition
                //
                "0bbe",
                "0bAe",
                "0b\te",
                "0b\u000ce",
                //
                "0ZAe",
                "0Z\te",
                "0Z\u000ce",
                "0Zbe",
                //
                "0\t\te",
                "0\t\u000ce",
                "0\tbe",
                "0\tAe",
                //
                "0\u000c\u000ce",
                "0\u000cbe",
                "0\u000cAe",
                "0\u000c\te",
                // two repetitions
                //
                "0bbbe",
                "0bbAe",
                "0bb\te",
                "0bb\u000ce",
                //
                "0bZAe",
                "0bZ\te",
                "0bZ\u000ce",
                "0bZbe",
                //
                "0b\t\te",
                "0b\t\u000ce",
                "0b\tbe",
                "0b\tAe",
                //
                "0b\u000c\u000ce",
                "0b\u000cbe",
                "0b\u000cAe",
                "0b\u000c\te",
                // fail EPs
                // one repetition
                //
                "0bbz",
                "0bAz",
                "0b\tz",
                "0b\u000cz",
                //
                "0ZAz",
                "0Z\tz",
                "0Z\u000cz",
                "0Zbz",
                //
                "0\t\tz",
                "0\t\u000cz",
                "0\tbz",
                "0\tAz",
                //
                "0\u000c\u000cz",
                "0\u000cbz",
                "0\u000cAz",
                "0\u000c\tz",
                // two repetitions
                //
                "0bbbz",
                "0bbAz",
                "0bb\tz",
                "0bb\u000cz",
                //
                "0bZAz",
                "0bZ\tz",
                "0bZ\u000cz",
                "0bZbz",
                //
                "0b\t\tz",
                "0b\t\u000cz",
                "0b\tbz",
                "0b\tAz",
                //
                "0b\u000c\u000cz",
                "0b\u000cbz",
                "0b\u000cAz",
                "0b\u000c\tz",
                // All fail self loops
                //
                "0ab",
                "AAA",
                "AeAA",
                "zzz",
                "00zz",
                // other's that i missed
                "\tz",
                "\u000cz",
                "bzzzz"
        ));
        for (AutomatonCoverage.EdgePair missing : coverage.missingFullMatchEdgePairs()) {
            System.out.println(missing);
        }
        assertFullMatchCoverage(
                coverage,
                info -> {},
                summary -> {
                    assertThat(summary.getEdgePairCoverage()).isEqualTo(1.0);
                }
        );
    }

    @Test
    public void productionPattern1_shouldNotHaveGt1NodeCoverage() {
        Automaton auto = prepareRegex("[\\d-.]+(\\w+)$");
        AutomatonCoverage coverage = new AutomatonCoverage(auto);
        coverageEvaluateAllIterable(coverage, Set.of("0", "10px", "16px", "1Q", "1cm", "1in", "1mm", "1pc", "1pt", "1px","1rem", "2em", "2rem", "50vh", "50vw"));
        assertFullMatchCoverage(
                coverage,
                info -> {},
                summary -> assertThat(summary.getNodeCoverage()).isLessThanOrEqualTo(1.0)
        );
    }

    @Test
    void productionPattern2_shouldNotFail() {
        Automaton auto = prepareRegex("^(.+?):(\\d+)(.*)$");
        AutomatonCoverage coverage = new AutomatonCoverage(auto);

        coverage.evaluate("hello:123");

        assertFullMatchCoverage(
                coverage,
                info -> {},
                summary -> assertThat(summary.getNodeCoverage()).isLessThanOrEqualTo(1.0)
        );
    }

    @Test
    void productionPattern3_shouldNotFail() {
        Automaton auto = prepareRegex("(?:\\b0x(?:[\\da-f]+\\.?[\\da-f]*|\\.[\\da-f]+)(?:p[+-]?\\d+)?|(?:\\b\\d+\\.?\\d*|\\B\\.\\d+)(?:e[+-]?\\d+)?)[ful]*");
        AutomatonCoverage coverage = new AutomatonCoverage(auto);

        coverage.evaluate("0xdead.beefp-123");

        assertFullMatchCoverage(
                coverage,
                info -> {},
                summary -> assertThat(summary.getNodeCoverage()).isLessThanOrEqualTo(1.0)
        );
    }

    private static Automaton prepareRegex(String pattern) {
        RegExp regex = new RegExp(pattern, RegExp.NONE);
        Automaton auto = regex.toAutomaton();
        auto.determinize();
        auto.minimize();
        return auto;
    }

    private static Set<Integer> statesToStateNums(Collection<State> states) {
        return states.stream().map(state -> state.number).collect(Collectors.toSet());
    }

    private static void assertFullMatchCoverage(AutomatonCoverage coverage,
                                       Consumer<AutomatonCoverage.VisitationInfo> onVisitationInfo,
                                       Consumer<AutomatonCoverage.VisitationInfoSummary> onVisitationInfoSummary) {

        onVisitationInfo.accept(coverage.getFullMatchVisitationInfo());
        onVisitationInfoSummary.accept(coverage.getFullMatchVisitationInfoSummary());
    }

    private static void assertPartialMatchCoverage(AutomatonCoverage coverage,
                                                Consumer<AutomatonCoverage.VisitationInfo> onVisitationInfo,
                                                Consumer<AutomatonCoverage.VisitationInfoSummary> onVisitationInfoSummary) {

        onVisitationInfo.accept(coverage.getPartialMatchVisitationInfo());
        onVisitationInfoSummary.accept(coverage.getPartialMatchVisitationInfoSummary());
    }

    private static void coverageEvaluateAllIterable(AutomatonCoverage coverage, Collection<String> strings) {
        strings.forEach(coverage::evaluate);
    }
}