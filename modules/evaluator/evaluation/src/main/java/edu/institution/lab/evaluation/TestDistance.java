package edu.institution.lab.evaluation;

import java.io.IOException;

import static edu.institution.lab.evaluation.distance.AstDistance.editDistance;

public class TestDistance {

    public static void notMain(String[] args) throws IOException {
        System.out.println("Testing identical regexes:");
        identicalRegex();

        System.out.println("Testing similar regexes:");
        similarRegex();

        System.out.println("Testing different regexes:");
        differentRegex();

        System.out.println("Testing Anonymous's examples:");
        anonymousExamples();
    }

    public static void testOutput(int testID, String s1, String s2, int dist) {
        System.out.println("Test " + testID);
        System.out.println("Regex 1: " + s1);
        System.out.println("Regex 2: " + s2);
        System.out.println("Distance: " + dist + "\n");
    }

    public static void identicalRegex() throws IOException {
        String regex1 = "[a-z]";
        testOutput(1, regex1, regex1, editDistance(regex1, regex1));

        String regex2 = "a+";
        testOutput(2, regex2, regex2, editDistance(regex2, regex2));

        String regex3 = "[a-z][A-Z][0-9]";
        testOutput(3, regex3, regex3, editDistance(regex3, regex3));

        String regex4 = "[a-z][\\w]*@.*";
        testOutput(4, regex4, regex4, editDistance(regex4, regex4));
    }

    public static void similarRegex() throws IOException {
        String regex1 = "a+";
        String regex2 = "a*";
        testOutput(1, regex1, regex2, editDistance(regex1, regex2));

        String regex3 = "[a-z]";
        String regex4 = "[a-e]";
        testOutput(2, regex3, regex4, editDistance(regex3, regex4));

        String regex5 = "[a-z]";
        String regex6 = "[A-Z]";
        testOutput(3, regex5, regex6, editDistance(regex5, regex6));

        String regex7 = "[a-z]";
        String regex8 = "[0-9]";
        testOutput(4, regex7, regex8, editDistance(regex7, regex8));

        String regex9 = "abc+";
        String regex10 = "abc*";
        testOutput(5, regex9, regex10, editDistance(regex9, regex10));
    }

    public static void differentRegex() throws IOException {
        String regex1 = "[a-z]";
        String regex2 = "a+";
        testOutput(1, regex1, regex2, editDistance(regex1, regex2));

        String regex3 = "[a-zA-Z0-9]";
        String regex4 = "abc*";
        testOutput(2, regex3, regex4, editDistance(regex3, regex4));
    }

    public static void anonymousExamples() throws IOException {
        String regex1 = "a+";
        String regex2 = "[abc]";
        String regex3 = "[abd]";
        String regex4 = "a";
        String regex5 = "abc*";
        String regex6 = "abc+";
        String regex7 = "b+";

        testOutput(1, regex1, regex1, editDistance(regex1, regex1));
        testOutput(2, regex1, regex7, editDistance(regex1, regex7));
        testOutput(2, regex2, regex3, editDistance(regex2, regex3));
        testOutput(3, regex5, regex6, editDistance(regex5, regex6));
        testOutput(4, regex1, regex4, editDistance(regex1, regex4));
    }

}
