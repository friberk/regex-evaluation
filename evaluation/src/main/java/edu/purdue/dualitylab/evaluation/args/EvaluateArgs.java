package edu.purdue.dualitylab.evaluation.args;

import com.beust.jcommander.Parameter;
import com.beust.jcommander.Parameters;

import java.util.Objects;

@Parameters(commandDescription = "Perform evaluation and save results")
public class EvaluateArgs {
    @Parameter(description = "Path to SQLite database containing test suites and static extraction results", required = true)
    private String databasePath;

    @Parameter(names = {"-u", "--updates-only"}, description = "only compute relative updates of existing test suite results")
    private Boolean coveragesOnly;

    public String getDatabasePath() {
        return databasePath;
    }

    public boolean isCoveragesOnly() {
        return Objects.requireNonNullElse(coveragesOnly, false);
    }
}
