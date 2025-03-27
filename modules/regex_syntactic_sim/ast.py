import re
from .PCRELexer import PCRELexer
from .PCREParser import PCREParser
from .PCREVisitor import PCREVisitor
from antlr4 import InputStream, CommonTokenStream

# A simple AST node class.
class ASTNode:
    def __init__(self, node_type, children=None, text=None):
        self.node_type = node_type
        self.children = children if children is not None else []
        self.text = text  # For leaf nodes

    def __str__(self, level=0):
        indent = "  " * level
        s = f"{indent}{self.node_type}"
        if self.text:
            s += f": {self.text}"
        s += "\n"
        for child in self.children:
            s += child.__str__(level+1)
        return s

# Custom visitor that builds an AST.
# It extends the generated PCREVisitor.
class PCREASTVisitor(PCREVisitor):
    # pcre: (alternation)? EOF
    def visitPcre(self, ctx:PCREParser.PcreContext):
        if ctx.alternation():
            return self.visit(ctx.alternation())
        return ASTNode("Empty")

    # alternation: expr ( Pipe expr )*
    def visitAlternation(self, ctx:PCREParser.AlternationContext):
        exprs = [self.visit(expr) for expr in ctx.expr()]
        if len(exprs) == 1:
            return exprs[0]
        return ASTNode("Alternation", exprs)

    # expr: element+
    def visitExpr(self, ctx:PCREParser.ExprContext):
        elements = [self.visit(el) for el in ctx.element()]
        if len(elements) == 1:
            return elements[0]
        return ASTNode("Concat", elements)

    # element: atom (quantifier)?
    def visitElement(self, ctx:PCREParser.ElementContext):
        node = self.visit(ctx.atom())
        if ctx.quantifier():
            quant = self.visit(ctx.quantifier())
            return ASTNode("Quantified", [node, quant])
        return node

    # For atom we use the default visitChildren.
    def visitAtom(self, ctx:PCREParser.AtomContext):
        return self.visitChildren(ctx)

    # Capture groups – for example, treat a capture as a “Capture” node.
    def visitCapture(self, ctx:PCREParser.CaptureContext):
        full_text = ctx.getText()
        # Check for inline option settings with a pattern like (?i:…)
        m = re.match(r'\(\?([idmsuxU-]+):', full_text)
        if m:
            # Extract the inline option letters (e.g. "i")
            option_string = m.group(1)
            # We consider this as a non-capturing group with options
            group_type = "NonCapture"
            option_node = ASTNode("OptionSetting", text=option_string)
            # Visit the inner alternation (or fall back to all children)
            inner = self.visit(ctx.alternation()) if ctx.alternation() else self.visitChildren(ctx)
            # Return a NonCapture node whose children are the OptionSetting and the inner pattern
            return ASTNode(group_type, [option_node, inner])
        elif full_text.startswith("(?:" ):
            # A plain non-capturing group without options
            group_type = "NonCapture"
            inner = self.visit(ctx.alternation()) if ctx.alternation() else self.visitChildren(ctx)
            return ASTNode(group_type, [inner])
        else:
            # A normal capture group
            group_type = "Capture"
            inner = self.visit(ctx.alternation()) if ctx.alternation() else self.visitChildren(ctx)
            return ASTNode(group_type, [inner])

    def visitAtomic_group(self, ctx:PCREParser.Atomic_groupContext):
        child = self.visit(ctx.alternation())
        return ASTNode("AtomicGroup", [child])

    def visitLookaround(self, ctx:PCREParser.LookaroundContext):
        # A lookaround typically starts with (?= or (?! etc.
        child = self.visit(ctx.alternation())
        return ASTNode("Lookaround", [child], text=ctx.start.text)

    def visitBackreference(self, ctx:PCREParser.BackreferenceContext):
        return ASTNode("Backreference", text=ctx.getText())

    def visitSubroutine_reference(self, ctx:PCREParser.Subroutine_referenceContext):
        return ASTNode("SubroutineReference", text=ctx.getText())

    def visitConditional_pattern(self, ctx:PCREParser.Conditional_patternContext):
        # If there is a "no_pattern" alternative, include it.
        cond = self.visit(ctx.expr(0))
        if ctx.no_pattern:
            no_pat = self.visit(ctx.no_pattern)
            return ASTNode("Conditional", [cond, no_pat])
        return ASTNode("Conditional", [cond])

    def visitComment(self, ctx:PCREParser.CommentContext):
        return ASTNode("Comment", text=ctx.getText())

    def visitQuantifier(self, ctx:PCREParser.QuantifierContext):
        return ASTNode("Quantifier", text=ctx.getText())

    def visitOption_setting(self, ctx:PCREParser.Option_settingContext):
        return ASTNode("OptionSetting", text=ctx.getText())

    def visitOption_setting_flag(self, ctx:PCREParser.Option_setting_flagContext):
        return ASTNode("OptionSettingFlag", text=ctx.getText())

    def visitBacktracking_control(self, ctx:PCREParser.Backtracking_controlContext):
        return ASTNode("BacktrackingControl", text=ctx.getText())

    def visitCallout(self, ctx:PCREParser.CalloutContext):
        return ASTNode("Callout", text=ctx.getText())

    def visitNewline_conventions(self, ctx:PCREParser.Newline_conventionsContext):
        return ASTNode("NewlineConventions", text=ctx.getText())

    def visitCharacter(self, ctx:PCREParser.CharacterContext):
        return ASTNode("Character", text=ctx.getText())

    def visitCharacter_type(self, ctx:PCREParser.Character_typeContext):
        return ASTNode("CharacterType", text=ctx.getText())

    def visitCharacter_class(self, ctx:PCREParser.Character_classContext):
        children = []
        # Use the token's text attribute instead of getText()
        if ctx.negate:
            children.append(ASTNode("Negate", text=ctx.negate.text))
        for atom in ctx.character_class_atom():
            children.append(self.visit(atom))
        return ASTNode("CharacterClass", children)

    def visitCharacter_class_atom(self, ctx:PCREParser.Character_class_atomContext):
        return ASTNode("CharacterClassAtom", text=ctx.getText())

    def visitCharacter_class_range(self, ctx:PCREParser.Character_class_rangeContext):
        left = self.visit(ctx.character_class_range_atom(0))
        right = self.visit(ctx.character_class_range_atom(1))
        return ASTNode("Range", [left, right])

    def visitPosix_character_class(self, ctx:PCREParser.Posix_character_classContext):
        return ASTNode("PosixCharacterClass", text=ctx.getText())

    def visitAnchor(self, ctx:PCREParser.AnchorContext):
        return ASTNode("Anchor", text=ctx.getText())

    def visitMatch_point_reset(self, ctx:PCREParser.Match_point_resetContext):
        return ASTNode("MatchPointReset", text=ctx.getText())

    def visitQuoting(self, ctx:PCREParser.QuotingContext):
        return ASTNode("Quoting", text=ctx.getText())

    def visitDigits(self, ctx:PCREParser.DigitsContext):
        return ASTNode("Digits", text=ctx.getText())

    def visitDigit(self, ctx:PCREParser.DigitContext):
        return ASTNode("Digit", text=ctx.getText())

    def visitHex(self, ctx:PCREParser.HexContext):
        return ASTNode("Hex", text=ctx.getText())

    def visitLetters(self, ctx:PCREParser.LettersContext):
        return ASTNode("Letters", text=ctx.getText())

    def visitLetter(self, ctx:PCREParser.LetterContext):
        return ASTNode("Letter", text=ctx.getText())

    def visitName(self, ctx:PCREParser.NameContext):
        return ASTNode("Name", text=ctx.getText())

    def visitOther(self, ctx:PCREParser.OtherContext):
        return ASTNode("Other", text=ctx.getText())

    def visitUtf(self, ctx:PCREParser.UtfContext):
        return ASTNode("UTF", text=ctx.getText())

    def visitUcp(self, ctx:PCREParser.UcpContext):
        return ASTNode("UCP", text=ctx.getText())

    def visitNo_auto_possess(self, ctx:PCREParser.No_auto_possessContext):
        return ASTNode("NoAutoPossess", text=ctx.getText())

    def visitNo_start_opt(self, ctx:PCREParser.No_start_optContext):
        return ASTNode("NoStartOpt", text=ctx.getText())

    def visitCr(self, ctx:PCREParser.CrContext):
        return ASTNode("CR", text=ctx.getText())

    def visitLf(self, ctx:PCREParser.LfContext):
        return ASTNode("LF", text=ctx.getText())

    def visitCrlf(self, ctx:PCREParser.CrlfContext):
        return ASTNode("CRLF", text=ctx.getText())

    def visitAnycrlf(self, ctx:PCREParser.AnycrlfContext):
        return ASTNode("AnyCRLF", text=ctx.getText())

    def visitAny(self, ctx:PCREParser.AnyContext):
        return ASTNode("Any", text=ctx.getText())

    def visitLimit_match(self, ctx:PCREParser.Limit_matchContext):
        return ASTNode("LimitMatch", text=ctx.getText())

    def visitLimit_recursion(self, ctx:PCREParser.Limit_recursionContext):
        return ASTNode("LimitRecursion", text=ctx.getText())

    def visitBsr_anycrlf(self, ctx:PCREParser.Bsr_anycrlfContext):
        return ASTNode("BSRAnyCRLF", text=ctx.getText())

    def visitBsr_unicode(self, ctx:PCREParser.Bsr_unicodeContext):
        return ASTNode("BSRUnicode", text=ctx.getText())

    def visitAccept_(self, ctx:PCREParser.Accept_Context):
        return ASTNode("Accept", text=ctx.getText())

    def visitFail(self, ctx:PCREParser.FailContext):
        return ASTNode("Fail", text=ctx.getText())

    def visitMark(self, ctx:PCREParser.MarkContext):
        return ASTNode("Mark", text=ctx.getText())

    def visitCommit(self, ctx:PCREParser.CommitContext):
        return ASTNode("Commit", text=ctx.getText())

    def visitPrune(self, ctx:PCREParser.PruneContext):
        return ASTNode("Prune", text=ctx.getText())

    def visitSkip(self, ctx:PCREParser.SkipContext):
        return ASTNode("Skip", text=ctx.getText())

    def visitThen(self, ctx:PCREParser.ThenContext):
        return ASTNode("Then", text=ctx.getText())

def regex_to_ast(regex):
    input_stream = InputStream(regex)
    lexer = PCRELexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    parser = PCREParser(token_stream)
    parser.removeErrorListeners()
    # Start parsing using the start rule "pcre"
    tree = parser.pcre()
    visitor = PCREASTVisitor()
    ast = visitor.visit(tree)
    return ast

def ast_to_regex(node):
    """
    Recursively convert an AST (made of ASTNode objects) back into a regex string.
    """
    # For nodes that simply carry literal text, return that text.
    if node.text is not None and not node.children:
        return node.text

    # Otherwise, switch based on the node type.
    if node.node_type == "Alternation":
        # Join each child with a '|'
        return "|".join(ast_to_regex(child) for child in node.children)
    elif node.node_type == "Concat":
        # Concatenate all children (implicit concatenation)
        return "".join(ast_to_regex(child) for child in node.children)
    elif node.node_type == "Capture":
        # A capture group is wrapped in parentheses.
        return "(" + ast_to_regex(node.children[0]) + ")"
    elif node.node_type == "NonCapture":
        # If there are inline options, assume the first child is options and the second is the inner expression.
        if len(node.children) > 1:
            options = ast_to_regex(node.children[0])
            inner   = "".join(ast_to_regex(child) for child in node.children[1:])
            return "(?" + options + ":" + inner + ")"
        else:
            return "(?:" + ast_to_regex(node.children[0]) + ")"
    elif node.node_type == "AtomicGroup":
        # Atomic groups are written as (?> ... )
        return "(?>" + ast_to_regex(node.children[0]) + ")"
    elif node.node_type == "Lookaround":
        # The node.text should hold the lookaround opener (like '(?=' or '(?!')
        # Append the inner expression and a closing parenthesis.
        return node.text + ast_to_regex(node.children[0]) + ")"
    elif node.node_type == "Conditional":
        # If there are two children, assume a pattern like (? (condition) | no_pattern )
        if len(node.children) == 2:
            return "(?(" + ast_to_regex(node.children[0]) + ")|" + ast_to_regex(node.children[1]) + ")"
        else:
            return "(?(" + ast_to_regex(node.children[0]) + "))"
    elif node.node_type == "Quantified":
        # Our visitor built a "Quantified" node with two children: the atom and its quantifier.
        return ast_to_regex(node.children[0]) + ast_to_regex(node.children[1])
    elif node.node_type == "Quantifier":
        return node.text  # e.g. '*', '+', '?', '{1,3}', etc.
    elif node.node_type == "CharacterClass":
        # For a character class, if the first child is a "Negate" node then include '^'
        inner = "".join(ast_to_regex(child) for child in node.children)
        return "[" + inner + "]"
    elif node.node_type == "Negate":
        # In our AST the Negate node simply holds the '^' token.
        return "^"
    # For many other nodes (e.g. Character, Letter, Digit, Name, Other, etc.)
    # we assume the node.text holds the literal text.
    elif node.text is not None:
        return node.text
    else:
        # Fallback: join all children.
        return "".join(ast_to_regex(child) for child in node.children)
