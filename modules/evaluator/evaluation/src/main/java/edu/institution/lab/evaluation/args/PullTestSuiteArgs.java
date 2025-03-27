package edu.institution.lab.evaluation.args;

import com.beust.jcommander.Parameter;
import com.beust.jcommander.Parameters;

import java.util.Objects;
import java.util.Optional;

@Parameters(commandDescription = "Pull test suites from database, categorize strings, compute coverages, and store them")
public class PullTestSuiteArgs {
    @Parameter(description = "Static extraction results database file", required = true)
    private String databaseFile;

    @Parameter(names = {"-o", "--json-output"}, description = "Optional path to write test suites in NDJSON format to")
    private String jsonOutputPath;

    @Parameter(names = { "-l", "--max-string-length" }, description = "Inclusive upper limit on test suite string length")
    private Integer maxStringLength;

    @Parameter(names = {"-u", "--update-coverage"}, description = "if flag is provided, only update coverages for test suites")
    private Boolean updateCoverages;

    public String getDatabaseFile() {
        return databaseFile;
    }

    public Optional<String> getJsonOutputPath() {
        return Optional.ofNullable(jsonOutputPath);
    }

    public Optional<Integer> getMaxStringLength() {
        return Optional.ofNullable(maxStringLength);
    }

    public boolean getUpdateCoverages() {
        return Objects.requireNonNullElse(updateCoverages, false);
    }
}
