package edu.purdue.dualitylab.evaluation.parser;

import edu.purdue.dualitylab.evaluation.PCRELexer;
import edu.purdue.dualitylab.evaluation.PCREParser;
import org.antlr.v4.runtime.CharStreams;
import org.antlr.v4.runtime.CommonTokenStream;
import org.antlr.v4.runtime.TokenStream;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

public class PCREParserTest {

    @Test
    void shouldParseCorrectly() {
        PCREParser.PcreContext context = parseRegex("[\\\\.\\?\\\\!]");
        assertThat(context).isNotNull();
    }

    @Test
    void shouldParseCorrectly2() {
        PCREParser.PcreContext context = parseRegex("\\/#\\");
        assertThat(context).isNotNull();
    }

    private static PCREParser.PcreContext parseRegex(String regex) {
        PCRELexer lexer = new PCRELexer(CharStreams.fromString(regex));
        TokenStream tokenStream = new CommonTokenStream(lexer);
        PCREParser parser = new PCREParser(tokenStream);
        return parser.pcre();
    }
}
