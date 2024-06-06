package edu.purdue.dualitylab.evaluation.args;

import com.beust.jcommander.Parameter;

public class RootArgs {
    @Parameter(names = {"-h", "--help"}, description = "Show usage", help = true)
    private Boolean help;

    public boolean getHelp() {
        if (help == null) {
            return false;
        }

        return help;
    }
}
