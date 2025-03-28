/*
 * Copyright (c) 2014-2023 by Bart Kiers
 *
 * The MIT license.
 *
 * Permission is hereby granted, free of charge, to any person
 * obtaining a copy of this software and associated documentation
 * files (the "Software"), to deal in the Software without
 * restriction, including without limitation the rights to use,
 * copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following
 * conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
 * OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
 * HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
 * WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
 * OTHER DEALINGS IN THE SOFTWARE.
 *
 * Project      : PCRE Parser, an ANTLR 4 grammar for PCRE
 * Developed by : Bart Kiers, bart@big-o.nl
 * Also see     : https://github.com/bkiers/pcre-parser
 *
 * Based on http://www.pcre.org/pcre.txt
 * (REVISION Last updated: 14 June 2021)
 */

// $antlr-format alignTrailingComments true, columnLimit 150, minEmptyLines 1, maxEmptyLinesToKeep 1, reflowComments false, useTab false
// $antlr-format allowShortRulesOnASingleLine false, allowShortBlocksOnASingleLine true, alignSemicolons hanging, alignColons hanging

grammar PCRE;

@header {
    package edu.institution.lab.evaluation;
}

pcre
    : alternation? EOF
    ;

alternation
    : expr ('|' expr?)*
    ;

expr
    : element+
    ;

element
    : atom quantifier?
    ;

atom
    : optionSetting
    | backtrackingControl
    | callout
    | capture
    | atomicGroup
    | lookaround
    | backreference
    | subroutineReference
    | conditionalPattern
    | comment
    | character
    | characterType
    | characterClass
    | posixCharacterClass
    | letter
    | digit
    | anchor
    | matchPointReset
    | quoting
    | other
    ;

capture
    : '(' (
        alternation
        | '?' (
            '<' name '>' alternation
            | '\'' name '\'' alternation
            | 'P' '<' name '>' alternation
            | ( optionSettingFlag+ ( '-' optionSettingFlag+)?)? ':' alternation
            | '|' alternation
        )
    ) ')'
    ;

atomicGroup
    : '(' '?' '>' alternation ')'
    ;

lookaround
    : '(' '?' ('=' | '!' | '<' '=' | '<' '!') alternation ')'
    ;

backreference
    : '\\' (
        'g' digits
        | 'g' '{' '-'? digits '}'
        | 'g' '{' name '}'
        | 'k' '<' name '>'
        | 'k' '\'' name '\''
        | 'k' '{' name '}'
    )
    | '(' '?' 'P' '=' name ')'
    ;

subroutineReference
    : '(' '?' ('R' | ( '+' | '-')? digits | '&' name | 'P' '>' name) ')'
    | '\\' 'g' (
        '<' name '>'
        | '\'' name '\''
        | '<' ( '+' | '-')? digits '>'
        | '\'' ( '+' | '-')? digits '\''
    )
    ;

conditionalPattern
    : '(' '?' (
        '(' (
            ( '+' | '-')? digits
            | '<' name '>'
            | '\'' name '\''
            | 'R' digits?
            | 'R' '&' name
            | name
        ) ')'
        | callout
        | lookaround
    ) expr ('|' noPattern = expr)? ')'
    ;

comment
    : '(' '?' '#' ~')'+ ')'
    ;

quantifier
    : ('?' | '*' | '+') (possessive = '+' | lazy = '?')?
    | '{' from = digits ( ',' to = digits?)? '}' ( possessive = '+' | lazy = '?')?
    ;

optionSetting
    : '(' (
        '*' (
            utf ( '8' | '1' '6' | '3' '2')?
            | ucp
            | noAutoPossess
            | noStartOpt
            | newlineConventions
            | limitMatch '=' digits
            | limitRecursion '=' digits
            | bsrAnycrlf
            | bsrUnicode
        )
        | '?' (optionSettingFlag+ ( '-' optionSettingFlag+)? | '-' optionSettingFlag+)
    ) ')'
    ;

optionSettingFlag
    : 'i'
    | 'J'
    | 'm'
    | 's'
    | 'U'
    | 'x'
    ;

backtrackingControl
    : '(' '*' (
        accept_
        | fail
        | mark? ':' name
        | commit
        | prune ( ':' name)?
        | skip ( ':' name)?
        | then ( ':' name)?
    ) ')'
    ;

callout
    : '(' '?' 'C' digits? ')'
    ;

newlineConventions
    : cr
    | lf
    | crlf
    | anycrlf
    | any
    ;

character
    : '\\' (
        'a'
        | 'c' .
        | 'e'
        | 'f'
        | 'n'
        | 'r'
        | 't'
        | digit (digit digit?)? // can also be a backreference
        | 'o' '{' digit digit digit+ '}'
        | 'x' hex hex
        | 'x' '{' hex hex hex+ '}'
        | 'u' hex hex hex hex ( hex hex hex hex)?
    )
    ;

characterType
    : '.'
    | '\\' (
        'C'
        | 'd'
        | 'D'
        | 'h'
        | 'H'
        | 'N'
        | 'p' '{' '^'? name '&'? '}'
        | 'P' '{' name '&'? '}'
        | 'p' letter letter?
        | 'R'
        | 's'
        | 'S'
        | 'v'
        | 'V'
        | 'w'
        | 'W'
        | 'X'
    )
    ;

characterClass
    : '[' negate = '^'? ']' characterClassAtom* ']'
    | '[' negate = '^'? characterClassAtom+ ']'
    ;

characterClassAtom
    : characterClassRange
    | posixCharacterClass
    | character
    | characterType
    | '\\' .
    | ~( '\\' | ']')
    ;

characterClassRange
    : characterClassRangeAtom '-' characterClassRangeAtom
    ;

characterClassRangeAtom
    : character
    | '\\' .
    | ~(']' | '\\')
    ;

posixCharacterClass
    : '[:' negate = '^'? letters ':]'
    ;

anchor
    : '\\' ('b' | 'B' | 'A' | 'z' | 'Z' | 'G')
    | '^'
    | '$'
    ;

matchPointReset
    : '\\' 'K'
    ;

quoting
    : '\\' ('Q' .*? '\\' 'E' | .)
    ;

// Helper rules
digits
    : digit+
    ;

digit
    : D0
    | D1
    | D2
    | D3
    | D4
    | D5
    | D6
    | D7
    | D8
    | D9
    ;

hex
    : digit
    | 'a'
    | 'b'
    | 'c'
    | 'd'
    | 'e'
    | 'f'
    | 'A'
    | 'B'
    | 'C'
    | 'D'
    | 'E'
    | 'F'
    ;

letters
    : letter+
    ;

letter
    : 'a'
    | 'b'
    | 'c'
    | 'd'
    | 'e'
    | 'f'
    | 'g'
    | 'h'
    | 'i'
    | 'j'
    | 'k'
    | 'l'
    | 'm'
    | 'n'
    | 'o'
    | 'p'
    | 'q'
    | 'r'
    | 's'
    | 't'
    | 'u'
    | 'v'
    | 'w'
    | 'x'
    | 'y'
    | 'z'
    | 'A'
    | 'B'
    | 'C'
    | 'D'
    | 'E'
    | 'F'
    | 'G'
    | 'H'
    | 'I'
    | 'J'
    | 'K'
    | 'L'
    | 'M'
    | 'N'
    | 'O'
    | 'P'
    | 'Q'
    | 'R'
    | 'S'
    | 'T'
    | 'U'
    | 'V'
    | 'W'
    | 'X'
    | 'Y'
    | 'Z'
    | '_'
    ;

name
    : letter (letter | digit)*
    ;

other
    : '}'
    | ']'
    | ','
    | '-'
    | '_'
    | '='
    | '&'
    | '<'
    | '>'
    | '\''
    | ':'
    | '#'
    | '!'
    | OTHER
    ;

utf
    : 'U' 'T' 'F'
    ;

ucp
    : 'U' 'C' 'P'
    ;

noAutoPossess
    : 'N' 'O' '_' 'A' 'U' 'T' 'O' '_' 'P' 'O' 'S' 'S' 'E' 'S' 'S'
    ;

noStartOpt
    : 'N' 'O' '_' 'S' 'T' 'A' 'R' 'T' '_' 'O' 'P' 'T'
    ;

cr
    : 'C' 'R'
    ;

lf
    : 'L' 'F'
    ;

crlf
    : 'C' 'R' 'L' 'F'
    ;

anycrlf
    : 'A' 'N' 'Y' 'C' 'R' 'L' 'F'
    ;

any
    : 'A' 'N' 'Y'
    ;

limitMatch
    : 'L' 'I' 'M' 'I' 'T' '_' 'M' 'A' 'T' 'C' 'H'
    ;

limitRecursion
    : 'L' 'I' 'M' 'I' 'T' '_' 'R' 'E' 'C' 'U' 'R' 'S' 'I' 'O' 'N'
    ;

bsrAnycrlf
    : 'B' 'S' 'R' '_' 'A' 'N' 'Y' 'C' 'R' 'L' 'F'
    ;

bsrUnicode
    : 'B' 'S' 'R' '_' 'U' 'N' 'I' 'C' 'O' 'D' 'E'
    ;

accept_
    : 'A' 'C' 'C' 'E' 'P' 'T'
    ;

fail
    : 'F' ('A' 'I' 'L')?
    ;

mark
    : 'M' 'A' 'R' 'K'
    ;

commit
    : 'C' 'O' 'M' 'M' 'I' 'T'
    ;

prune
    : 'P' 'R' 'U' 'N' 'E'
    ;

skip
    : 'S' 'K' 'I' 'P'
    ;

then
    : 'T' 'H' 'E' 'N'
    ;

/// \      general escape character with several uses
BSlash
    : '\\'
    ;

/// $      assert end of string (or line, in multiline mode)
Dollar
    : '$'
    ;

/// .      match any character except newline (by default)
Dot
    : '.'
    ;

/// [      start character class definition
OBrack
    : '['
    ;

/// ^      assert start of string (or line, in multiline mode)
Caret
    : '^'
    ;

/// |      start of alternative branch
Pipe
    : '|'
    ;

/// ?      extends the meaning of (, also 0 or 1 quantifier.txt, also quantifier.txt minimizer
QMark
    : '?'
    ;

/// *      0 or more quantifier.txt
Star
    : '*'
    ;

/// +      1 or more quantifier.txt, also "possessive quantifier.txt"
Plus
    : '+'
    ;

/// {      start min/max quantifier.txt
OBrace
    : '{'
    ;

CBrace
    : '}'
    ;

/// (      start subpattern
OPar
    : '('
    ;

/// )      end subpattern
CPar
    : ')'
    ;

/// ]      terminates the character class
CBrack
    : ']'
    ;

OPosixBrack
    : '[:'
    ;

CPosixBrack
    : ':]'
    ;

Comma
    : ','
    ;

Dash
    : '-'
    ;

UScore
    : '_'
    ;

Eq
    : '='
    ;

Amp
    : '&'
    ;

Lt
    : '<'
    ;

Gt
    : '>'
    ;

Quote
    : '\''
    ;

Col
    : ':'
    ;

Hash
    : '#'
    ;

Excl
    : '!'
    ;

Au
    : 'A'
    ;

Bu
    : 'B'
    ;

Cu
    : 'C'
    ;

Du
    : 'D'
    ;

Eu
    : 'E'
    ;

Fu
    : 'F'
    ;

Gu
    : 'G'
    ;

Hu
    : 'H'
    ;

Iu
    : 'I'
    ;

Ju
    : 'J'
    ;

Ku
    : 'K'
    ;

Lu
    : 'L'
    ;

Mu
    : 'M'
    ;

Nu
    : 'N'
    ;

Ou
    : 'O'
    ;

Pu
    : 'P'
    ;

Qu
    : 'Q'
    ;

Ru
    : 'R'
    ;

Su
    : 'S'
    ;

Tu
    : 'T'
    ;

Uu
    : 'U'
    ;

Vu
    : 'V'
    ;

Wu
    : 'W'
    ;

Xu
    : 'X'
    ;

Yu
    : 'Y'
    ;

Zu
    : 'Z'
    ;

Al
    : 'a'
    ;

Bl
    : 'b'
    ;

Cl
    : 'c'
    ;

Dl
    : 'd'
    ;

El
    : 'e'
    ;

Fl
    : 'f'
    ;

Gl
    : 'g'
    ;

Hl
    : 'h'
    ;

Il
    : 'i'
    ;

Jl
    : 'j'
    ;

Kl
    : 'k'
    ;

Ll
    : 'l'
    ;

Ml
    : 'm'
    ;

Nl
    : 'n'
    ;

Ol
    : 'o'
    ;

Pl
    : 'p'
    ;

Ql
    : 'q'
    ;

Rl
    : 'r'
    ;

Sl
    : 's'
    ;

Tl
    : 't'
    ;

Ul
    : 'u'
    ;

Vl
    : 'v'
    ;

Wl
    : 'w'
    ;

Xl
    : 'x'
    ;

Yl
    : 'y'
    ;

Zl
    : 'z'
    ;

D0
    : '0'
    ;

D1
    : '1'
    ;

D2
    : '2'
    ;

D3
    : '3'
    ;

D4
    : '4'
    ;

D5
    : '5'
    ;

D6
    : '6'
    ;

D7
    : '7'
    ;

D8
    : '8'
    ;

D9
    : '9'
    ;

OTHER
    : .
    ;
