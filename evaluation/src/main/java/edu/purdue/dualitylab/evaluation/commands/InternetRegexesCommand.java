package edu.purdue.dualitylab.evaluation.commands;

import edu.purdue.dualitylab.evaluation.args.InternetRegexesArgs;
import edu.purdue.dualitylab.evaluation.args.RootArgs;
import edu.purdue.dualitylab.evaluation.db.RegexDatabaseClient;
import edu.purdue.dualitylab.evaluation.internet.InternetEvaluationService;
import edu.purdue.dualitylab.evaluation.internet.StackOverflowRegexPost;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.sqlite.SQLiteConfig;

import java.io.File;
import java.sql.Connection;
import java.sql.DriverManager;
import java.util.Collection;

public class InternetRegexesCommand extends AbstractCommand<InternetRegexesArgs, Void> {

    private static final Logger logger = LoggerFactory.getLogger(InternetRegexesCommand.class);

    private final SQLiteConfig sqliteConfig;

    public InternetRegexesCommand(RootArgs rootArgs, InternetRegexesArgs internetRegexesArgs, SQLiteConfig sqliteConfig) {
        super(rootArgs, internetRegexesArgs);
        this.sqliteConfig = sqliteConfig;
    }

    @Override
    public Void call() throws Exception {
        String regexDbPath = String.format("jdbc:sqlite:%s", args.getRegexDatabasePath());
        logger.info("connecting to regex database at ");
        Connection regexConnection = DriverManager.getConnection(regexDbPath, this.sqliteConfig.toProperties());
        RegexDatabaseClient regexDatabaseClient = new RegexDatabaseClient(regexConnection);
        logger.info("Successfully connected to regex database");

        String internetDbPath = String.format("jdbc:sqlite:%s", args.getInternetRegexDatabasePath());
        logger.info("connecting to regex database at ");
        Connection internetConnection = DriverManager.getConnection(internetDbPath, this.sqliteConfig.toProperties());
        RegexDatabaseClient internetRegexDatabaseClient = new RegexDatabaseClient(internetConnection);
        logger.info("Successfully connected to regex database");

        InternetEvaluationService internetEvaluationService = new InternetEvaluationService(internetRegexDatabaseClient, regexDatabaseClient);
        if (args.isLoadPostsFromFileAndSaveToDb()) {
            logger.info("Starting to load and save StackOverflow post regexes");
            File outputFile = new File(args.getInternetRegexDatabasePath());
            internetEvaluationService.loadCandidatesFromFileAndSave(outputFile);
            logger.info("done");
        }

        internetEvaluationService.evaluateInternetRegexes();

        return null;
    }
}
