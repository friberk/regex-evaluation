package dk.brics.automaton;

import java.util.ArrayList;
import java.util.Collection;
import java.util.HashSet;
import java.util.Random;
import java.util.Set;
import java.util.function.Function;
import java.util.function.Predicate;
import java.util.regex.Pattern;
import java.util.stream.Collectors;
import java.util.stream.IntStream;

public class GenerateStrings {

    public static final class GenerateStringsConfiguration {
        private final boolean generatePositive;
        private final int maxNumVisits;
        private final int characterClassSampleCount;

        public GenerateStringsConfiguration() {
            this(true, 3, 0);
        }

        public GenerateStringsConfiguration(boolean generatePositive, int maxNumVisits, int characterClassSampleCount) {
            this.generatePositive = generatePositive;
            this.maxNumVisits = maxNumVisits;
            this.characterClassSampleCount = characterClassSampleCount;
        }

        public GenerateStringsConfiguration withMaxNumVisits(Function<Integer, Integer> transformer) {
            int newVisitMax = transformer.apply(this.maxNumVisits);
            if (newVisitMax == this.maxNumVisits) {
                return this;
            }

            return new GenerateStringsConfiguration(generatePositive, newVisitMax, this.characterClassSampleCount);
        }

        public GenerateStringsConfiguration withMaxNumVisits(int newVisitMax) {
            return this.withMaxNumVisits((unused) -> newVisitMax);
        }

        public GenerateStringsConfiguration withGeneratePositiveStrings(boolean genPositive) {
            if (isGeneratePositive() ^ genPositive) {
                return this;
            }

            return new GenerateStringsConfiguration(genPositive, this.maxNumVisits, this.characterClassSampleCount);
        }

        public boolean isGeneratePositive() {
            return generatePositive;
        }

        public int getMaxNumVisits() {
            return maxNumVisits;
        }

        public int getCharacterClassSampleCount() {
            return characterClassSampleCount;
        }

        public boolean isTakeAll() {
            return characterClassSampleCount <= 0;
        }
    }

    /**
     * Finds an estimation of all the strings a regular expression can match with
     * @param regExpStr String representation of a regex
     * @return ArrayList containing positive strings for the regex
     * @throws IllegalArgumentException might be due to parsing, or regex is too large to estimate
     */
    public static Set<String> generateStrings(String regExpStr, GenerateStringsConfiguration configuration) throws IllegalArgumentException {
        RegExp regExp = new RegExp(regExpStr);
        Automaton automaton = regExp.toAutomaton();
        return generateStrings(automaton, configuration);
    }

    /**
     * Finds an estimation of all the strings a regular expression can match with
     * @param regexAuto String representation of a regex
     * @return ArrayList containing positive strings for the regex
     * @throws IllegalArgumentException regex is too large to estimate
     */
    public static Set<String> generateStrings(Automaton regexAuto, GenerateStringsConfiguration configuration) throws IllegalArgumentException {
        ArrayList<State> path = new ArrayList<>();
        Set<String> strings = new HashSet<>();

        if (configuration.isGeneratePositive()) {
            traverse(regexAuto.getInitialState(), path, strings, configuration);
        }
        else {
            Automaton autoCompliment = regexAuto.complement();
            traverse(autoCompliment.getInitialState(), path, strings, configuration);
        }
        return strings;
    }


    private static void traverse(State curr, ArrayList<State> path, Set<String> strings, GenerateStringsConfiguration config) throws IllegalArgumentException {

        ArrayList<State> currPath = shallowCopy(path);
        currPath.add(curr);
        curr.numVisits++;

        try {
            if (curr.isAccept()) {
                addPathToList(currPath, strings, config);
            }
            for (Transition t : curr.getTransitions()) {
                if (t.getDest().numVisits < config.getMaxNumVisits()) {
                    if (curr.equals(t.getDest())) {
                        GenerateStringsConfiguration reducedVisitsConfig = config.withMaxNumVisits(originalValue -> originalValue / 2);
                        traverse(t.getDest(), currPath, strings, reducedVisitsConfig);
                    }
                    else {
                        traverse(t.getDest(), currPath, strings, config);
                    }
                }
            }
        }
        catch (OutOfMemoryError | IllegalArgumentException e) {
            throw new IllegalArgumentException("Cannot approximate language of regex", e);
        }
        catch (Exception e) {
            throw new RuntimeException("Cannot approximate language of regex, but for a reason i can't think of", e);
        }
    }

    /**
     * Finds the e-similarity score between two regular expressions
     *
     * @param truthRegexStr     String representation of the truth regex
     * @param reuseCandidateStr String representation of the reuse candidate regex
     * @return e-similarity score as a float (between 0 and 1)
     */
    public static double eSimilarity(String truthRegexStr, String reuseCandidateStr, GenerateStringsConfiguration config) {

        Set<String> truthPositiveStr = generateStrings(truthRegexStr, config.withGeneratePositiveStrings(true));
        Set<String> truthNegativeStr = generateStrings(truthRegexStr, config.withGeneratePositiveStrings(false));
        Pattern reuseCandidateRegex = Pattern.compile(reuseCandidateStr);
        Predicate<String> tester = (inputString) -> {
            if (config.isGeneratePositive()) {
                return reuseCandidateRegex.matcher(inputString).matches();
            } else {
                return reuseCandidateRegex.matcher(inputString).find();
            }
        };

        return eSimilarity(truthPositiveStr, truthNegativeStr, tester);
    }

    /**
     * More generalized esimilarity function. Takes in a set of positive and negative strings from the truth regex
     * and a predicate that determines if a reuse candidate matches a string or not. The matchClassifier is used
     * to classify the positive/negative strings, and an esimilarity score is reported
     *
     * @param truthPositiveStr Collection of positive/matching strings
     * @param truthNegativeStr Collection of negative/mis-matching strings
     * @param matchClassifier A predicate that determines if a reuse candidate matches the provided string
     * @return esimilarity score
     */
    public static double eSimilarity(Collection<String> truthPositiveStr, Collection<String> truthNegativeStr, Predicate<String> matchClassifier) {
        int numPositiveStr = truthPositiveStr.size();
        int numNegativeStr = truthNegativeStr.size();
        int numMatches = 0;
        int numRejects = 0;
        for (String positiveStr : truthPositiveStr) {
            if (matchClassifier.test(positiveStr)) {
                numMatches++;
            }
        }
        for (String negativeStr : truthNegativeStr) {
            if (!matchClassifier.test(negativeStr)) {
                numRejects++;
            }
        }

        return eSimilarity(numMatches, numRejects, numPositiveStr, numNegativeStr);
    }

    public static double eSimilarity(int numMatches, int numRejects, int positiveStringCount, int negativeStringCount) {
        return ((double) (numMatches + numRejects) / (positiveStringCount + negativeStringCount));
    }

    private static ArrayList<State> shallowCopy(ArrayList<State> path) {
        return new ArrayList<>(path);
    }

    private static void addPathToList(ArrayList<State> path, Set<String> strings, GenerateStringsConfiguration config) {
        ArrayList<String> pathStrings = new ArrayList<>();
        for (int i = 0; i < path.size() - 1; i++) {
            ArrayList<Transition> transitions = findTransitions(path.get(i), path.get(i + 1));
            pathStrings = addCharacters(transitions, pathStrings, config);
        }
        strings.addAll(pathStrings);
    }


    private static ArrayList<Transition> findTransitions(State currState, State destState) {
        ArrayList<Transition> transitions = new ArrayList<>();
        for (Transition t : currState.getTransitions()) {
            if (t.getDest().equals(destState)) {
                transitions.add(t);
            }
        }
        return transitions;
    }


    private static ArrayList<String> addCharacters(ArrayList<Transition> transitions, ArrayList<String> pathStrings, GenerateStringsConfiguration config) {
        ArrayList<String> newPathStrings = new ArrayList<>();
        Collection<Character> charsToAppend = getCharsToAppend(transitions, config);

        // adding characters
        if (!pathStrings.isEmpty()) {
            for (String s : pathStrings) {
                for (Character c : charsToAppend) {
                    newPathStrings.add(s + c);
                }
            }
        } else {
            for (Character c : charsToAppend) {
                newPathStrings.add(c.toString());
            }
        }
        return newPathStrings;
    }

    private static Collection<Character> getCharsToAppend(ArrayList<Transition> transitions, GenerateStringsConfiguration config) {
        Set<Character> charsToAppend = new HashSet<>();

        // TODO astonishment...
        int sampleCount = config.isGeneratePositive() ? config.getCharacterClassSampleCount() : 1;
        for (Transition t : transitions) {
            charsToAppend.addAll(sampleTransitionCharacters(t, sampleCount));
        }

        return charsToAppend;
    }

    private static Set<Character> sampleTransitionCharacters(Transition transition, int sampleCount) {
        // get the range we actually want to sample
        Pair<Character, Character> sampleRange = sliceRangeToUnicode(transition);
        char sampleRangeLower = sampleRange.getLeft();
        char sampleRangeUpper = sampleRange.getRight();

        return sampleTransitionCharacters(sampleRangeLower, sampleRangeUpper, sampleCount);
    }

    private static Set<Character> sampleTransitionCharacters(char lower, char upper, int maxCharCount) {

        int transitionCharacterCount = upper - lower + 1; // plus one cause it includes max
        if (maxCharCount <= 0 || transitionCharacterCount <= maxCharCount) {
            return IntStream.rangeClosed(lower, upper)
                    .mapToObj(ival -> (char) ival)
                    .collect(Collectors.toSet());
        }

        // otherwise, we need to sample
        Set<Character> characterSample = new HashSet<>();
        Random random = new Random();
        while (characterSample.size() < maxCharCount) {
            int randomCharacterInt = random.nextInt((int) upper - (int) lower) + (int) lower;
            characterSample.add((char) randomCharacterInt);
        }

        return characterSample;
    }

    private static Pair<Character, Character> sliceRangeToUnicode(Transition transition) {
        return sliceRangeToUnicode(transition.getMin(), transition.getMax());
    }

    /**
     * Given a range of characters, try to slice down to only pleasant unicode characters. If the character range
     * is entirely outside unicode, then return the range unchanged
     * @param transitionLower Transition lower bound
     * @param transitionUpper transition upper bound, inclusive
     * @return Pair of characters representing inclusive sliced range
     */
    private static Pair<Character, Character> sliceRangeToUnicode(char transitionLower, char transitionUpper) {
        int minRangeValue;
        int maxRangeValue;
        // 0x007e = , 0x0020 =
        if (transitionLower > 0x007e || transitionUpper < 0x0020) {
            minRangeValue = transitionLower;
            maxRangeValue = transitionUpper;
        } else {
            minRangeValue = Math.max(transitionLower, 0x0020);
            maxRangeValue = Math.min(transitionUpper, 0x007e);
        }

        return Pair.of((char) minRangeValue, (char) maxRangeValue);
    }
}
