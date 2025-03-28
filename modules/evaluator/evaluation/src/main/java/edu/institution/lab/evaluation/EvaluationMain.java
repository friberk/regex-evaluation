package edu.institution.lab.evaluation;

import com.beust.jcommander.JCommander;
import edu.institution.lab.evaluation.args.*;
import edu.institution.lab.evaluation.commands.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.sqlite.SQLiteConfig;

/**
 * Main entry point to the applications. Parses command line arguments, sets up some basic shared config, and then
 * dispatches down to a specific sub-command.
 */
public class EvaluationMain {

    private final static Logger logger = LoggerFactory.getLogger(EvaluationMain.class);

    public static void main(String[] args) throws Exception {
        RootArgs rootArgs = new RootArgs();
        PullTestSuiteArgs pullTestSuiteArgs = new PullTestSuiteArgs();
        EvaluateArgs evaluateArgs = new EvaluateArgs();
        UpdateDistancesArgs updateDistancesArgs = new UpdateDistancesArgs();
        InternetRegexesArgs internetRegexesArgs = new InternetRegexesArgs();
        ManualQueryArgs manualQueryArgs = new ManualQueryArgs();
        JCommander jc = JCommander.newBuilder()
                .addObject(rootArgs)
                .addCommand("pull-test-suites", pullTestSuiteArgs)
                .addCommand("evaluate", evaluateArgs)
                .addCommand("update-distances", updateDistancesArgs)
                .addCommand("internet-evaluation", internetRegexesArgs)
                .addCommand("manual-query", manualQueryArgs)
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

            case "update-distances":
                UpdateDistancesCommand updateDistancesCommand = new UpdateDistancesCommand(rootArgs, updateDistancesArgs, dbConfig);
                updateDistancesCommand.call();
                break;

            case "internet-evaluation":
                InternetRegexesCommand internetRegexesCommand = new InternetRegexesCommand(rootArgs, internetRegexesArgs, dbConfig);
                internetRegexesCommand.call();
                break;

            case "manual-query":
                ManualQueryCommand manualQueryCommand = new ManualQueryCommand(rootArgs, manualQueryArgs, dbConfig);
                manualQueryCommand.call();
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
