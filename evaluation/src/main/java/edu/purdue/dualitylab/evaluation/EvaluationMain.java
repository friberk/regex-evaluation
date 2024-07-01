package edu.purdue.dualitylab.evaluation;

import com.beust.jcommander.JCommander;
import edu.purdue.dualitylab.evaluation.args.EvaluateArgs;
import edu.purdue.dualitylab.evaluation.args.PullTestSuiteArgs;
import edu.purdue.dualitylab.evaluation.args.RootArgs;
import edu.purdue.dualitylab.evaluation.commands.EvaluateCommand;
import edu.purdue.dualitylab.evaluation.commands.PullTestSuitesCommand;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.sqlite.SQLiteConfig;

public class EvaluationMain {

    private final static Logger logger = LoggerFactory.getLogger(EvaluationMain.class);

    public static void main(String[] args) throws Exception {
        RootArgs rootArgs = new RootArgs();
        PullTestSuiteArgs pullTestSuiteArgs = new PullTestSuiteArgs();
        EvaluateArgs evaluateArgs = new EvaluateArgs();
        JCommander jc = JCommander.newBuilder()
                .addObject(rootArgs)
                .addCommand("pull-test-suites", pullTestSuiteArgs)
                .addCommand("evaluate", evaluateArgs)
                .build();

        jc.parse(args);

        if (rootArgs.getHelp()) {
            jc.usage();
            System.exit(0);
        }

        SQLiteConfig dbConfig = sqliteConfig(rootArgs.getTempStoreMode());

        switch (jc.getParsedCommand()) {
            case "pull-test-suites":
                PullTestSuitesCommand pullTestSuitesCmd = new PullTestSuitesCommand(rootArgs, pullTestSuiteArgs, dbConfig);
                pullTestSuitesCmd.call();
                break;

            case "evaluate":
                EvaluateCommand evaluateCmd = new EvaluateCommand(rootArgs, evaluateArgs, dbConfig);
                evaluateCmd.call();
                break;

            default:
                throw new RuntimeException(String.format("Command %s is not supported", jc.getParsedCommand()));
        }
    }

    public static SQLiteConfig sqliteConfig(SQLiteConfig.TempStore tempStore) {
        SQLiteConfig config = new SQLiteConfig();
        config.enableLoadExtension(true);
        config.setTempStore(tempStore);
        config.setSynchronous(SQLiteConfig.SynchronousMode.OFF);
        return config;
    }
}
