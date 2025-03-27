package edu.institution.lab.evaluation.distance.ast;

import edu.institution.lab.evaluation.PCREBaseVisitor;
import edu.institution.lab.evaluation.PCREParser;
import org.antlr.v4.runtime.ParserRuleContext;
import org.antlr.v4.runtime.tree.ParseTree;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class ZhangShashaTreeBuilder extends PCREBaseVisitor<Node> {

    private static Map<Character, String> SYMBOL_MAP = null;

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

    static {
        SYMBOL_MAP = buildSymbolMap();
    }

    private static String changeSymbol(String s) {
        StringBuilder result = new StringBuilder();

        for (char c : s.toCharArray()) {
            if (SYMBOL_MAP.containsKey(c)) {
                result.append(SYMBOL_MAP.get(c));
            } else {
                result.append(c);
            }
        }

        return result.toString();
    }

    private final PCREParser parser;

    public ZhangShashaTreeBuilder(PCREParser parser) {
        this.parser = parser;
    }

    @Override
    public Node visit(ParseTree tree) {
        String label = getLabel(tree);
        List<Node> children = new ArrayList<>();
        for (int i = 0; i < tree.getChildCount(); i++) {
            ParseTree child = tree.getChild(i);
            Node childNode = visit(child);
            children.add(childNode);
        }

        Node node = new Node(label);
        node.children.addAll(children);

        return node;
    }

    private String getLabel(ParseTree node) {
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
