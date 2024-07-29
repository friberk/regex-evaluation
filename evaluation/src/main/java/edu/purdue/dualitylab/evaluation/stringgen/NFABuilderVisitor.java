package edu.purdue.dualitylab.evaluation.stringgen;

import edu.purdue.dualitylab.evaluation.PCREBaseVisitor;
import edu.purdue.dualitylab.evaluation.PCREParser;
import edu.purdue.dualitylab.evaluation.util.Pair;

import java.util.List;

/**
 * Builds an "NFA" from base visitor
 */
public class NFABuilderVisitor extends PCREBaseVisitor<NFA> {

    private static class CharacterClassAtomVisitor extends PCREBaseVisitor<Pair<Character, Character>> {

    }


    @Override
    public NFA visitAlternation(PCREParser.AlternationContext ctx) {
        List<NFA> branches = ctx.expr().stream()
                .map(this::visit)
                .toList();

        if (branches.isEmpty()) {
            return NFA.empty();
        } else if (branches.size() == 1) {
            return branches.get(0);
        } else {
            return NFABuilders.alternation(branches);
        }
    }

    @Override
    public NFA visitExpr(PCREParser.ExprContext ctx) {
        List<NFA> elementNFAs = ctx.element().stream()
                .map(this::visit)
                .toList();

        return NFABuilders.concat(elementNFAs);
    }

    @Override
    public NFA visitElement(PCREParser.ElementContext ctx) {
        NFA atomNFA = visit(ctx.atom());
        if (ctx.quantifier() != null) {
            PCREParser.QuantifierContext qty = ctx.quantifier();
            // figure out quantifier
            atomNFA = NFABuilders.quantifier(atomNFA, extractQuantifierInfo(qty));
        }

        return atomNFA;
    }

    @Override
    public NFA visitAtom(PCREParser.AtomContext ctx) {
        return super.visitAtom(ctx);
    }

    @Override
    public NFA visitLetter(PCREParser.LetterContext ctx) {
        char letter = ctx.getText().charAt(0);
        return NFABuilders.literal(letter);
    }

    @Override
    public NFA visitDigit(PCREParser.DigitContext ctx) {
        char digit = ctx.getText().charAt(0);
        return NFABuilders.literal(digit);
    }

    @Override
    public NFA visitAtomicGroup(PCREParser.AtomicGroupContext ctx) {
        return visit(ctx.alternation());
    }

    @Override
    public NFA visitCapture(PCREParser.CaptureContext ctx) {
        return visit(ctx.alternation());
    }

    @Override
    public NFA visitCharacterClass(PCREParser.CharacterClassContext ctx) {
        ctx.characterClassAtom().stream()
                .map(atom -> {
                    if (atom.characterClassRange() != null) {
                        var range = atom.characterClassRange();
                    }
                })
    }

    @Override
    public NFA visitCharacterType(PCREParser.CharacterTypeContext ctx) {
        if (ctx.Dot() != null) {
            return NFABuilders.literal(Character.MIN_VALUE, Character.MAX_VALUE);
        }

        if (ctx.Dl() != null) {

        }
    }

    private QuantifierInfo extractQuantifierInfo(PCREParser.QuantifierContext qty) {
        QuantifierInfo quantifierInfo = null;
        if (qty.Plus() != null) {
            quantifierInfo = QuantifierInfo.plus();
        } else if (qty.Star() != null) {
            quantifierInfo = QuantifierInfo.star();
        } else if (qty.QMark() != null) {
            quantifierInfo = QuantifierInfo.questionMark();
        } else if (!qty.digits().isEmpty()) {
            int lower = Integer.parseInt(qty.digits(0).getText());
            Integer upper = null;
            if (qty.digits().size() > 1) {
                upper = Integer.parseInt(qty.digits(1).getText());
            }
            if (upper == null) {
                if (qty.Comma() != null) {
                    quantifierInfo = QuantifierInfo.atLeast(lower);
                } else {
                    quantifierInfo = QuantifierInfo.exactly(lower);
                }
            } else {
                quantifierInfo = QuantifierInfo.bounded(lower, upper);
            }
        }

        return quantifierInfo;
    }
}
