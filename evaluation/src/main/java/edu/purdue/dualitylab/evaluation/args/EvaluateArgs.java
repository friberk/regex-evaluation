package edu.purdue.dualitylab.evaluation.args;

import com.beust.jcommander.Parameter;
import com.beust.jcommander.Parameters;

@Parameters(commandDescription = "Perform evaluation and save results")
public class EvaluateArgs {
    @Parameter(description = "Path to SQLite database containing test suites and static extraction results", required = true)
    private String databasePath;

    public String getDatabasePath() {
        return databasePath;
    }
}
