package edu.purdue.dualitylab.evaluation.args;

import com.beust.jcommander.Parameter;
import com.beust.jcommander.Parameters;

import java.util.OptionalInt;

@Parameters(commandDescription = "Update distance measures for results")
public class UpdateDistancesArgs {

    @Parameter(names = {"-m", "--max-length"}, description = "Max length allowed for regexes. Any regex longer than this will fail to compute")
    private Integer maxRegexLength;

    @Parameter(names = {"-d", "--max-distance"}, description = "Max difference in lengths between truth and candidate. Any regex length difference larger than this will fail to compute")
    private Integer maxRegexDistance;

    @Parameter(description = "Path to SQLite database containing test suites and static extraction results", required = true)
    private String databasePath;

    public String getDatabasePath() {
        return databasePath;
    }

    public OptionalInt getMaxRegexLength() {
        if (maxRegexLength == null) {
            return OptionalInt.empty();
        } else {
            return OptionalInt.of(maxRegexLength);
        }
    }

    public OptionalInt getMaxRegexDistance() {
        if (maxRegexDistance == null) {
            return OptionalInt.empty();
        } else {
            return OptionalInt.of(maxRegexDistance);
        }
    }
}
