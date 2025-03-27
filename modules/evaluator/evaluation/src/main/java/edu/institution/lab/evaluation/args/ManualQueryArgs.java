package edu.institution.lab.evaluation.args;

import com.beust.jcommander.Parameter;
import com.beust.jcommander.Parameters;

import java.util.Objects;

@Parameters(commandDescription = "Find reuse candidates for manually provided regex")
public class ManualQueryArgs {
    @Parameter(names = {"-f", "--full-match"}, description = "If the argument is specified, perform full match operation. Otherwise, perform partial match operation")
    private Boolean fullMatch;

    @Parameter(names = {"-d", "--database"}, description = "Path to database file containing reuse candidates")
    private String databasePath;

    @Parameter(names = {"-o", "--output"}, description = "path to write results to in NDJSON format")
    private String outputPath;

    @Parameter(description = "Path to NDJSON file containing test suites")
    private String testSuiteFile;

    public boolean getFullMatch() {
        return Objects.requireNonNullElse(fullMatch, false);
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
