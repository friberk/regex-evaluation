package edu.purdue.dualitylab.evaluation.stringgen;

import edu.purdue.dualitylab.evaluation.util.Pair;

import java.util.*;
import java.util.stream.Collectors;

public final class NFABuilders {
    public static NFA alternation(Collection<NFA> nfas) {
        NFA parent = new NFA();
        int rootState = parent.addRootState();
        Set<Integer> branchEndStates = new HashSet<>();
        for (NFA nfa : nfas) {
            int branchEndState = parent.concatNFA(rootState, nfa, NFAEdge.epsilon());
            branchEndStates.add(branchEndState);
        }

        // link all together into new accept state
        int acceptState = parent.addAcceptState();

        for (int endState : branchEndStates) {
            parent.addEdge(endState, acceptState, NFAEdge.epsilon());
        }

        return parent;
    }

    public static NFA concat(NFA left, NFA right) {
        int lastState = left.getAcceptState();
        left.concatNFAWithOverlappingState(lastState, right);
        return left;
    }

    public static NFA concat(List<NFA> nfas) {
        if (nfas.isEmpty()) {
            return NFA.empty();
        }

        if (nfas.size() == 1) {
            return nfas.get(0);
        }

        NFA collect = nfas.remove(0);
        for (NFA nfa : nfas) {
            collect = concat(collect, nfa);
        }

        return collect;
    }

    public static NFA quantifier(NFA nfa, QuantifierInfo quantifierInfo) {
        NFA kleenNFA = new NFA();
        int rootState = kleenNFA.addRootState();
        int nfaEnd = kleenNFA.concatNFA(rootState, nfa, new NFAEdge(quantifierInfo, NFAEdge.QuantifierEnd.START));
        int newAcceptState = kleenNFA.addAcceptState();
        kleenNFA.addEdge(nfaEnd, newAcceptState, new NFAEdge(quantifierInfo, NFAEdge.QuantifierEnd.END));
        return kleenNFA;
    }

    public static NFA negCharacterClass(Collection<Pair<Character, Character>> ranges, Set<Character> alphabet) {
        Set<Character> selectedRanges = ranges.stream()
                .flatMap(range -> {
                    Set<Character> characters = new HashSet<>();
                    for (char c = range.a(); c <= range.b(); c++) {
                        characters.add(c);
                    }

                    return characters.stream();
                })
                .collect(Collectors.toSet());

        alphabet.removeAll(selectedRanges);

        // if there is nothing left, then we can just make an empty nfa
        if (alphabet.isEmpty()) {
            return NFA.empty();
        }

        List<Pair<Character, Character>> alphabetRanges = new ArrayList<>();
        List<Character> includedCharacters = new ArrayList<>(alphabet);
        int start = 0;
        char last = 0;
        int end = 0;
        for (int i = 0; i < includedCharacters.size(); i++) {
            char current = includedCharacters.get(i);
            // set initial value
            if (i == 0) {
                last = current;
                continue;
            }

            // if current value and last value are adjacent (off by one), then bump the end range
            if (current - last == 1) {
                end++;
            } else {
                alphabetRanges.add(Pair.of(includedCharacters.get(start), includedCharacters.get(end)));
                start = i;
                end = i;
            }

            last = current;
        }

        alphabetRanges.add(Pair.of(includedCharacters.get(start), includedCharacters.get(end)));

        return characterClass(alphabetRanges);
    }

    public static NFA characterClass(Collection<Pair<Character, Character>> ranges) {
        NFA nfa = new NFA();
        int start = nfa.addRootState();
        int end = nfa.addAcceptState();
        ranges.stream()
                .map(rangePair -> new NFAEdge(rangePair.a(), rangePair.b(), QuantifierInfo.exactly(1), NFAEdge.QuantifierEnd.SINGLE))
                .forEach(edge -> nfa.addEdge(start, end, edge));

        return nfa;
    }

    public static NFA literal(char single) {
        return literal(new NFAEdge(single, QuantifierInfo.exactly(1), NFAEdge.QuantifierEnd.START));
    }

    public static NFA literal(char lower, char upper) {
        return literal(new NFAEdge(lower, upper, QuantifierInfo.exactly(1), NFAEdge.QuantifierEnd.START));
    }

    private static NFA literal(NFAEdge edge) {
        NFA nfa = new NFA();
        int root = nfa.addRootState();
        int accept = nfa.addAcceptState();
        nfa.addEdge(root, accept, edge);
        return nfa;
    }
}
