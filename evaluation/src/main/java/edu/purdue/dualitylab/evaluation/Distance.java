package edu.purdue.dualitylab.evaluation;

import edu.purdue.dualitylab.evaluation.PCRELexer;
import edu.purdue.dualitylab.evaluation.PCREParser;
import org.antlr.v4.runtime.*;
import org.antlr.v4.runtime.tree.ParseTree;
import org.antlr.v4.runtime.tree.ParseTreeWalker;
import org.antlr.v4.gui.TreeViewer;

import java.util.Collection;
import java.util.HashSet;
import java.util.Set;

import javax.swing.*;
import java.util.Arrays;

public class Distance {

    public static void editDistance(String r1, String r2) {

        // building the ASTs for both regexps
        PCRELexer lexer1 = new PCRELexer(CharStreams.fromString(r1));
        TokenStream tokens1 = new CommonTokenStream(lexer1);
        PCREParser parser1 = new PCREParser(tokens1);
        ParseTree regexTree1 = parser1.pcre();

        PCRELexer lexer2 = new PCRELexer(CharStreams.fromString(r2));
        TokenStream tokens2 = new CommonTokenStream(lexer2);
        PCREParser parser2 = new PCREParser(tokens2);
        ParseTree regexTree2 = parser2.pcre();

        // Print the trees to the console
        System.out.println("Parse tree for r1:");
        System.out.println(regexTree1.toStringTree(parser1));
        System.out.println("Parse tree for r2:");
        System.out.println(regexTree2.toStringTree(parser2));
    }

    public static void main(String[] args) {
        if (args.length != 2) {
            System.out.println("Usage: Distance <r1> <r2>");
        }

        String r1 = "[a-z]";
        String r2 = "[a-e]";
        editDistance(r1, r2);
    }
}

