package edu.purdue.dualitylab.evaluation.args;

import com.beust.jcommander.Parameter;
import com.beust.jcommander.ParameterException;
import com.beust.jcommander.Parameters;

import java.util.Optional;

@Parameters(commandDescription = "Pull test suites from database, categorize strings, compute coverages, and store them")
public class PullTestSuiteArgs {

    private static final String SQLITE_REGEX_EXTENSION_PATH = "SQLITE_REGEX_EXTENSION_PATH";

    @Parameter(description = "Static extraction results database file", required = true)
    private String databaseFile;

    @Parameter(names = {"-o", "--json-output"}, description = "Optional path to write test suites in NDJSON format to")
    private String jsonOutputPath;

    @Parameter(names = "--extension", description = "Path to regex sqlite extension. Optionally set by SQLITE_REGEX_EXTENSION_PATH env variable")
    private String extensionPath;

    public String getDatabaseFile() {
        return databaseFile;
    }

    public Optional<String> getJsonOutputPath() {
        return Optional.ofNullable(jsonOutputPath);
    }

    public String getExtensionPath() {
        return Optional.ofNullable(this.extensionPath)
                .or(() -> Optional.ofNullable(System.getenv(SQLITE_REGEX_EXTENSION_PATH)))
                .orElseThrow(() -> new ParameterException(String.format("Failed to set sqlite regex extensions path: wasn't provided, and wasn't in env under %s", SQLITE_REGEX_EXTENSION_PATH)));
    }
}
