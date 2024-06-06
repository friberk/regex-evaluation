package edu.purdue.dualitylab.evaluation.commands;

import edu.purdue.dualitylab.evaluation.args.EvaluateArgs;
import edu.purdue.dualitylab.evaluation.db.RegexDatabaseClient;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.sqlite.SQLiteConfig;

import java.sql.Connection;
import java.sql.DriverManager;

public class EvaluateCommand extends AbstractCommand<EvaluateArgs, Void> {

    private static final Logger logger = LoggerFactory.getLogger(EvaluateCommand.class);
    private final SQLiteConfig sqliteConfig;

    public EvaluateCommand(EvaluateArgs args, SQLiteConfig sqliteConfig) {
        super(args);
        this.sqliteConfig = sqliteConfig;
    }

    @Override
    public Void call() throws Exception {

        String dbPath = String.format("jdbc:sqlite:%s", args.getDatabasePath());
        logger.info("connecting to database at ");
        Connection connection = DriverManager.getConnection(dbPath, this.sqliteConfig.toProperties());
        RegexDatabaseClient regexDatabaseClient = new RegexDatabaseClient(connection);
        logger.info("Successfully connected to database");



        return null;
    }
}
