package parsers.java;

import com.github.javaparser.JavaParser;
import com.github.javaparser.ParseResult;
import com.github.javaparser.ParseStart;
import com.github.javaparser.Providers;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.symbolsolver.javaparsermodel.JavaParserFacade;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

public class RegexExtractorManager {

    private final JavaParserFactory parserFactory;
    private final RegexExtractor regexExtractor;

    public RegexExtractorManager(JavaParserFactory factory) {
        this.parserFactory = factory;
        this.regexExtractor = new RegexExtractor();
    }

    public List<RegexObject> parseRegexObjects(File inputFile) {
        List<RegexObject> regexObjects = new ArrayList<>();
        try {
            JavaParser javaParser = parserFactory.create();
            System.out.println("Starting to parse file...");
            ParseResult<CompilationUnit> compilationUnit = javaParser.parse(ParseStart.COMPILATION_UNIT, Providers.provider(inputFile));
            compilationUnit.ifSuccessful(compUnit -> regexExtractor.visit(compUnit, regexObjects));
            return regexObjects;
        } catch (IOException e) {
            // if we encounter an io exception, just skip it by returning an empty list
            return List.of();
        } finally {
            // clear cache after each invocation
            JavaParserFacade.clearInstances();
        }
    }
}
