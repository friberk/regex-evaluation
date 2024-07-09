package edu.purdue.dualitylab.evaluation.args;

import com.beust.jcommander.Parameter;
import com.beust.jcommander.Parameters;

@Parameters(commandDescription = "Update distance measures for results")
public class UpdateDistancesArgs {
    @Parameter(description = "Path to SQLite database containing test suites and static extraction results", required = true)
    private String databasePath;

    public String getDatabasePath() {
        return databasePath;
    }
}
