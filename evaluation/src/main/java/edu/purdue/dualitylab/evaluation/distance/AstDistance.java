package edu.purdue.dualitylab.evaluation.distance;

import edu.purdue.dualitylab.evaluation.PCRELexer;
import edu.purdue.dualitylab.evaluation.PCREParser;
import edu.purdue.dualitylab.evaluation.distance.ast.Node;
import edu.purdue.dualitylab.evaluation.distance.ast.Tree;
import edu.purdue.dualitylab.evaluation.distance.ast.ZhangShasha;
import edu.purdue.dualitylab.evaluation.distance.ast.ZhangShashaTreeBuilder;
import org.antlr.v4.runtime.*;
import org.antlr.v4.runtime.tree.ParseTree;
import org.antlr.v4.runtime.ParserRuleContext;

import java.io.IOException;
import java.util.*;

/**
 * Compute the AST edit distance between strings.
 */
public class AstDistance {

    public static Tree buildTree(String regex) {
        regex = regex.trim();
        PCRELexer lexer = new PCRELexer(CharStreams.fromString(regex));
        TokenStream tokens = new CommonTokenStream(lexer);
        PCREParser parser = new PCREParser(tokens);
        ParseTree tree = parser.pcre();
        ZhangShashaTreeBuilder builder = new ZhangShashaTreeBuilder(parser);
        Node rootNode = builder.visit(tree);
        return new Tree(rootNode);
    }

    public static int editDistance(String regex1, String regex2) {
        Tree regexTree1 = buildTree(regex1);
        return editDistance(regexTree1, regex2);
    }

    public static int editDistance(Tree truthTree, String candidatePattern) {
        Tree candidateTree = buildTree(candidatePattern);
        return editDistance(truthTree, candidateTree);
    }

    public static int editDistance(Tree truthTree, Tree candidateTree) {
        return ZhangShasha.editDistance(truthTree, candidateTree);
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
}

