package edu.purdue.dualitylab.evaluation.args;

import com.beust.jcommander.Parameter;
import com.beust.jcommander.Parameters;

import java.util.Objects;

@Parameters(commandDescription = "Find reuse candidates for manually provided regex")
public class ManualQueryArgs {
    @Parameter(names = {"-f", "--full-match"}, description = "If true, perform full match operation. If false, perform partial match")
    private Boolean fullMatch;

    @Parameter(names = {"-d", "--database"}, description = "Path to database file containing reuse candidates")
    private String databasePath;

    @Parameter(names = {"-o", "--output"}, description = "path to write results to in NDJSON format")
    private String outputPath;

    @Parameter(description = "Path to file containing test suite")
    private String testSuiteFile;

    public boolean getFullMatch() {
        return Objects.requireNonNullElse(fullMatch, true);
    }

    public String getDatabasePath() {
        return databasePath;
    }

    public String getTestSuiteFile() {
        return testSuiteFile;
    }

    public String getOutputPath() {
        return outputPath;
    }
}
