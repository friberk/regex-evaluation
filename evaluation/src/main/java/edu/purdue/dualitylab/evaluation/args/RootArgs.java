package edu.purdue.dualitylab.evaluation.args;

import com.beust.jcommander.Parameter;
import com.beust.jcommander.ParameterException;

import java.util.Optional;

public class RootArgs {

    private static final String SQLITE_REGEX_EXTENSION_PATH = "SQLITE_REGEX_EXTENSION_PATH";

    @Parameter(names = {"-h", "--help"}, description = "Show usage", help = true)
    private Boolean help;

    @Parameter(names = "--extension", description = "Path to regex sqlite extension. Optionally set by SQLITE_REGEX_EXTENSION_PATH env variable")
    private String extensionPath;

    public boolean getHelp() {
        if (help == null) {
            return false;
        }

        return help;
    }

    public String getExtensionPath() {
        return Optional.ofNullable(this.extensionPath)
                .or(() -> Optional.ofNullable(System.getenv(SQLITE_REGEX_EXTENSION_PATH)))
                .orElseThrow(() -> new ParameterException(String.format("Failed to set sqlite regex extensions path: wasn't provided, and wasn't in env under %s", SQLITE_REGEX_EXTENSION_PATH)));
    }
}
