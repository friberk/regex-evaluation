package edu.purdue.dualitylab.evaluation;

import com.beust.jcommander.JCommander;
import edu.purdue.dualitylab.evaluation.args.PullTestSuiteArgs;
import edu.purdue.dualitylab.evaluation.args.RootArgs;
import edu.purdue.dualitylab.evaluation.commands.PullTestSuitesCommand;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.sqlite.SQLiteConfig;

public class EvaluationMain {

    private final static Logger logger = LoggerFactory.getLogger(EvaluationMain.class);

    public static void main(String[] args) throws Exception {
        RootArgs rootArgs = new RootArgs();
        PullTestSuiteArgs pullTestSuiteArgs = new PullTestSuiteArgs();
        JCommander jc = JCommander.newBuilder()
                .addObject(rootArgs)
                .addCommand("pull-test-suites", pullTestSuiteArgs)
                .build();

        jc.parse(args);

        if (rootArgs.getHelp()) {
            jc.usage();
            System.exit(0);
        }

        switch (jc.getParsedCommand()) {
            case "pull-test-suites":
                PullTestSuitesCommand cmd = new PullTestSuitesCommand(pullTestSuiteArgs, sqliteConfig());
                cmd.call();
                break;

            default:
                throw new RuntimeException(String.format("Command %s is not supported", jc.getParsedCommand()));
        }
    }

    public static SQLiteConfig sqliteConfig() {
        SQLiteConfig config = new SQLiteConfig();
        config.enableLoadExtension(true);
        config.setSynchronous(SQLiteConfig.SynchronousMode.OFF);
        return config;
    }
}
