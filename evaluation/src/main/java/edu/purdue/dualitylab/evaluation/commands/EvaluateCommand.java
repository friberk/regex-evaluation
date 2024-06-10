package edu.purdue.dualitylab.evaluation.commands;

import edu.purdue.dualitylab.evaluation.evaluation.EvaluationService;
import edu.purdue.dualitylab.evaluation.args.EvaluateArgs;
import edu.purdue.dualitylab.evaluation.args.RootArgs;
import edu.purdue.dualitylab.evaluation.db.RegexDatabaseClient;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.sqlite.SQLiteConfig;

import java.sql.Connection;
import java.sql.DriverManager;

public class EvaluateCommand extends AbstractCommand<EvaluateArgs, Void> {

    private static final Logger logger = LoggerFactory.getLogger(EvaluateCommand.class);
    private final SQLiteConfig sqliteConfig;

    public EvaluateCommand(RootArgs rootArgs, EvaluateArgs args, SQLiteConfig sqliteConfig) {
        super(rootArgs, args);
        this.sqliteConfig = sqliteConfig;
    }

    @Override
    public Void call() throws Exception {

        String dbPath = String.format("jdbc:sqlite:%s", args.getDatabasePath());
        logger.info("connecting to database at ");
        Connection connection = DriverManager.getConnection(dbPath, this.sqliteConfig.toProperties());
        RegexDatabaseClient regexDatabaseClient = new RegexDatabaseClient(connection);
        logger.info("Successfully connected to database");

        regexDatabaseClient.initDatabase(rootArgs.getExtensionPath());
        logger.info("Starting to load test suites...");

        EvaluationService service = new EvaluationService(regexDatabaseClient);

        var results = service.evaluateTestSuites();

        logger.info("Saving test suite results....");
        regexDatabaseClient.insertManyTestSuiteResults(results);
        logger.info("Done");

        regexDatabaseClient.close();

        return null;
    }
}
