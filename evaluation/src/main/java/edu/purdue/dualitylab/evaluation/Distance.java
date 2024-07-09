package edu.purdue.dualitylab.evaluation;

import edu.purdue.dualitylab.evaluation.distance.ast.Tree;
import org.antlr.v4.runtime.*;
import org.antlr.v4.runtime.tree.ParseTree;
import org.antlr.v4.runtime.ParserRuleContext;

import java.io.IOException;
import java.util.*;

public class Distance {

    public static int editDistance(String regex1, String regex2) throws IOException {
        String regexString1 = buildTree(regex1);
        String regexString2 = buildTree(regex2);

        Tree regexTree1 = new Tree(regexString1);
        Tree regexTree2 = new Tree(regexString2);

        return Tree.ZhangShasha(regexTree1, regexTree2);
    }

    public static int editDistance(Tree truthTree, String candidatePattern) throws IOException {
        String candidateString = buildTree(candidatePattern);
        Tree candidateTree = new Tree(candidateString);
        return Tree.ZhangShasha(candidateTree, truthTree);
    }

    private static Map<Character, String> symbolMap = null;

    private static Map<Character, String> buildSymbolMap() {
        Map<Character, String> symbolMap = new HashMap<>();
        symbolMap.put('*', "asterisk");
        symbolMap.put('+', "plus");
        symbolMap.put('$', "dollarSign");
        symbolMap.put('&', "ampersand");
        symbolMap.put('@', "atSign");
        symbolMap.put('#', "hash");
        symbolMap.put('%', "percent");
        symbolMap.put('^', "caret");
        symbolMap.put('(', "leftParenthesis");
        symbolMap.put(')', "rightParenthesis");
        symbolMap.put('-', "hyphen");
        symbolMap.put('_', "underscore");
        symbolMap.put('=', "equals");
        symbolMap.put('{', "leftBrace");
        symbolMap.put('}', "rightBrace");
        symbolMap.put('[', "leftBracket");
        symbolMap.put(']', "rightBracket");
        symbolMap.put('|', "verticalBar");
        symbolMap.put('\\', "backslash");
        symbolMap.put(':', "colon");
        symbolMap.put(';', "semicolon");
        symbolMap.put('"', "doubleQuote");
        symbolMap.put('\'', "singleQuote");
        symbolMap.put('<', "lessThan");
        symbolMap.put('>', "greaterThan");
        symbolMap.put(',', "comma");
        symbolMap.put('.', "dot");
        symbolMap.put('/', "slash");
        symbolMap.put('?', "questionMark");
        symbolMap.put('!', "exclamationMark");
        symbolMap.put('~', "tilde");
        symbolMap.put('`', "backtick");
        symbolMap.put('0', "zero");
        symbolMap.put('1', "one");
        symbolMap.put('2', "two");
        symbolMap.put('3', "three");
        symbolMap.put('4', "four");
        symbolMap.put('5', "five");
        symbolMap.put('6', "six");
        symbolMap.put('7', "seven");
        symbolMap.put('8', "eight");
        symbolMap.put('9', "nine");
        return symbolMap;
    }

    private static String changeSymbol(String s) {
        StringBuilder result = new StringBuilder();

        for (char c : s.toCharArray()) {
            if (symbolMap.containsKey(c)) {
                result.append(symbolMap.get(c));
            } else {
                result.append(c);
            }
        }

        return result.toString();
    }

    private static String getLabel(ParseTree node, PCREParser parser) {
        // if node is a rule
        if (node instanceof ParserRuleContext) {
            int ruleIndex = ((ParserRuleContext) node).getRuleIndex();
            return parser.getRuleNames()[ruleIndex];
        // if node is a character or atom
        } else {
            return changeSymbol(node.getText());
        }
    }

    private static void traverse(ParseTree node, StringBuilder sb, PCREParser parser) {
        if (node == null) {
            return;
        }

        // adding the correct label to the string
        sb.append(getLabel(node, parser));

        if (node.getChildCount() > 0) {
            sb.append("(");
            for (int i = 0; i < node.getChildCount(); i++) {
                traverse(node.getChild(i), sb, parser);
                if (i < node.getChildCount() - 1) {
                    sb.append(" ");
                }
            }
            sb.append(")");
        }
    }

    private static String buildTree(String s) {

        // removing leading and trailing whitespace
        s = s.trim();

        // building the parse tree from the string
        PCRELexer lexer = new PCRELexer(CharStreams.fromString(s));
        TokenStream tokens = new CommonTokenStream(lexer);
        PCREParser parser = new PCREParser(tokens);
        ParseTree tree = parser.pcre();

        // traversing the tree to format string correctly
        StringBuilder sb = new StringBuilder();
        if (symbolMap == null) {
            symbolMap = buildSymbolMap();
        }
        traverse(tree, sb, parser);

        return sb.toString().trim();
    }
}

