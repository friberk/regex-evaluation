package edu.institution.lab.evaluation.commands;

import edu.institution.lab.evaluation.evaluation.EvaluationService;
import edu.institution.lab.evaluation.args.EvaluateArgs;
import edu.institution.lab.evaluation.args.RootArgs;
import edu.institution.lab.evaluation.db.RegexDatabaseClient;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.sqlite.SQLiteConfig;

import java.sql.Connection;
import java.sql.DriverManager;

/**
 * The evaluate command performs the evaluation for our reuse-by-example database. It is responsible for finding reuse
 * candidates for each test suite. Additionally, it computes coverages. You should run `pull-test-suites` before
 * running this command.
 * <br>
 * Optionally, you can just compute relative coverages for each test suite with the previously computed reuse
 * candidates.
 */
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
        EvaluationService service = new EvaluationService(regexDatabaseClient);

        if (!args.isCoveragesOnly()) {
            logger.info("Starting to evaluate test suites...");
            service.evaluateAndSaveTestSuites();
        }

        logger.info("Starting to evaluate relative coverages");
        service.updateRelativeCoverages();

        regexDatabaseClient.close();

        logger.info("Successfully evaluated test suites");

        return null;
    }
}
