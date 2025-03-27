package parsers.java;

import com.github.javaparser.JavaParser;
import com.github.javaparser.ParserConfiguration;
import com.github.javaparser.symbolsolver.JavaSymbolSolver;
import com.github.javaparser.symbolsolver.resolution.typesolvers.CombinedTypeSolver;

public final class JavaParserFactory {
    private final ParserConfiguration config;

    public JavaParserFactory() {
        this(new ParserConfiguration());
    }

    public JavaParserFactory(ParserConfiguration config) {
        this.config = config;
    }

    public JavaParser create() {
        CombinedTypeSolver combinedSolver = new CombinedTypeSolver();
        JavaSymbolSolver symbolSolver = new JavaSymbolSolver(combinedSolver);
        JavaParser javaParser = new JavaParser(config);
        javaParser.getParserConfiguration().setSymbolResolver(symbolSolver);
        return javaParser;
    }
}
