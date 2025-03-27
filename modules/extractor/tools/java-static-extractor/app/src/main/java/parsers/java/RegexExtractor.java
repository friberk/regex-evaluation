package parsers.java;

import com.github.javaparser.ast.NodeList;
import com.github.javaparser.ast.expr.Expression;
import com.github.javaparser.ast.expr.MethodCallExpr;
import com.github.javaparser.ast.expr.NameExpr;
import com.github.javaparser.ast.expr.StringLiteralExpr;
import com.github.javaparser.ast.visitor.VoidVisitorAdapter;
import com.github.javaparser.resolution.declarations.ResolvedMethodDeclaration;
import com.github.javaparser.resolution.declarations.ResolvedValueDeclaration;
import com.github.javaparser.resolution.types.ResolvedType;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.List;
import java.util.Optional;
import java.util.regex.Matcher;

public class RegexExtractor extends VoidVisitorAdapter<List<RegexObject>> {

    private static final Logger logger = LoggerFactory.getLogger(RegexExtractor.class);

    /**
     * @returns: String or null
     */
    private static String getFirstArgIfLiteralString(NodeList<Expression> methodCallArgs) {
        Expression arg = methodCallArgs.get(0);
        if (arg.isStringLiteralExpr()) {
            StringLiteralExpr patternStr = arg.asStringLiteralExpr();
            return patternStr.getValue();
        } else {
            logger.error("arg0 className: <{}>", arg.getClass().getName());
            return null;
        }
    }

    private static boolean isScopedMethodCall(MethodCallExpr expr) {
        Optional<Expression> scopeName = expr.getScope();
        return scopeName.isPresent();
    }

    private static boolean isStringType(NameExpr nameExpr) {
        try {
            logger.debug(" ne: Resolving");
            ResolvedValueDeclaration rvd = nameExpr.resolve();
            logger.debug(" ne: Getting type");
            ResolvedType type = rvd.getType();
            if (type.describe().equals("java.lang.String")) {
                return true;
            }
        } catch (Exception e) {
            logger.debug(" >>> Exception: Could not resolve NameExpr");
            return false;
        }
        return false;
    }

    private static boolean isStringType(MethodCallExpr mcExpr) {
        try {
            logger.debug(" mce: Resolving");
            ResolvedMethodDeclaration rmd = mcExpr.resolve();
            logger.debug(" mce: Getting type");
            ResolvedType type = rmd.getReturnType();
            if (type.describe().equals("java.lang.String")) {
                return true;
            }
        } catch (Exception e) {
            logger.debug(" >>> Exception: Could not resolve MethodCallExpr");
            return false;
        }
        return false;
    }

    private static boolean isMethodCallInStringScope(MethodCallExpr expr) {
        if (isScopedMethodCall(expr)) {
            logger.debug("  scope: {}", expr.getScope());
            logger.debug("  scope Expression type: {}", expr.getScope().get().getClass().getName());
            Expression scope = expr.getScope().get();
            if (scope.isStringLiteralExpr()) {
                // If the scope is a string literal, then we are in String scope by definition
                logger.debug("Scope is StringLiteralExpr");
                return true;
            } else if (scope.isNameExpr()) {
                logger.debug("Scope is NameExpr");
                NameExpr ne_scope = scope.asNameExpr();
                return isStringType(ne_scope);
            } else if (scope.isMethodCallExpr()) {
                MethodCallExpr mce_scope = scope.asMethodCallExpr();
                return isStringType(mce_scope);
            } else {
                // System.err.println("Unknown scope type");
                return false;
            }
        }
        //System.err.println("  scope ResolvedType: " + expr.getScope().calculateResolvedType().describe());
        logger.debug("  name: {}", expr.getName());
        return false;
    }

    private static boolean isMethodCallInPatternScope(MethodCallExpr expr) {
        // Pattern.compile and Pattern.matches are static, so the scope is easy to identify.
        // This assumes, of course, that the user never names a variable 'Pattern' or defines
        // their own class with this name. Probably a safe assumption?
        if (isScopedMethodCall(expr)) {
            String scopeName = expr.getScope().get().toString();
            logger.debug(" scopeName: {}", scopeName);
            return scopeName.equals("Pattern") || scopeName.equals("java.util.regex.Pattern");
        }
        return false;
    }

    private static boolean isCallTo(MethodCallExpr expr, String method) {
        return expr.getName().asString().equals(method);
    }

    private static boolean isCallToMatches(MethodCallExpr expr) {
        return expr.getName().asString().equals("matches");
    }

    /**
     * Convert pattern to a "raw string".
     * This matches how most other languages declare regexes.
     */
    public static String unescapePattern(String pattern) {
        // Java really needs raw strings! This replaces '\\' with '\'
        String replacement = pattern.replaceAll(Matcher.quoteReplacement("\\\\"), Matcher.quoteReplacement("\\"));
        logger.debug("unescapePattern: /{}/ --> /{}/", pattern, replacement);
        return replacement;
    }

    @Override
    public void visit(MethodCallExpr expr, List<RegexObject> regexList) {
        super.visit(expr, regexList);

        logger.debug("MethodCallExpr: {}", expr);
        boolean callDefinesARegex = false;
        String pattern = null;
        if (isMethodCallInStringScope(expr)) {
            logger.debug("  Method call in String scope");
            if (isCallTo(expr, "matches")
                    || isCallTo(expr, "split")
                    || isCallTo(expr, "replaceFirst")
                    || isCallTo(expr, "replaceAll"))
            {
                logger.debug("  String.{matches | split | replaceFirst | replaceAll}");
                callDefinesARegex = true;
                // Each of these has a regex as the first arg
                NodeList<Expression> args = expr.getArguments();
                if (args.size() >= 1) {
                    pattern = getFirstArgIfLiteralString(args);
                }
            }
        }
        else if (isMethodCallInPatternScope(expr)) {
            logger.debug("  Method call in Pattern scope");
            if (isCallTo(expr, "compile")) {
                logger.debug("  Pattern.compile");
                NodeList<Expression> args = expr.getArguments();
                if (args.size() == 1 || args.size() == 2) {
                    // Pattern.compile: Pattern.compile(String pattern[, int flags])
                    callDefinesARegex = true;
                    logger.debug(" Pattern.compile(pattern[, flags])");
                    pattern = getFirstArgIfLiteralString(args);
                    // TODO We could retrieve flags if we wanted, for args.size() > 1.
                }
            } else if (isCallToMatches(expr)) {
                System.err.println("  Pattern.matches");
                NodeList<Expression> args = expr.getArguments();
                if (args.size() == 2) {
                    // Pattern.matches(String pattern, String input)
                    callDefinesARegex = true;
                    pattern = getFirstArgIfLiteralString(args);
                }
            }
        }
        // If call defines a regex but arg is not a literal string, it is DYNAMIC
        if (callDefinesARegex && pattern == null) {
            logger.debug("Call defines a regex, but the regex is not a string literal");
            pattern = "DYNAMIC";
        }

        // Values for pattern at this point:
        //   null            A method call that does not create a regex
        //   DYNAMIC         A method call that creates a regex, but with a non-StringLiteral expression
        //   anything else   A method call that creates a regex with a static string
        if (pattern != null) {
            // get the location of the regex
            int lineNo = expr.getBegin().map(loc -> loc.line).orElse(0);

            pattern = unescapePattern(pattern);
            logger.debug(" << Regex declaration: regex /" + pattern + "/");
            regexList.add(new RegexObject(pattern, "UNKNOWN", lineNo, "TODO FIXME"));
        }
    }
}
