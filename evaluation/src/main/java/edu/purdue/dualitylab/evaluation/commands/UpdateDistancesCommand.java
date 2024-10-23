package edu.purdue.dualitylab.evaluation.commands;

import edu.purdue.dualitylab.evaluation.args.RootArgs;
import edu.purdue.dualitylab.evaluation.args.UpdateDistancesArgs;
import edu.purdue.dualitylab.evaluation.db.RegexDatabaseClient;
import edu.purdue.dualitylab.evaluation.distance.UpdateDistancesService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.sqlite.SQLiteConfig;

import java.sql.Connection;
import java.sql.DriverManager;
import java.util.function.BiPredicate;
import java.util.function.Predicate;

/**
 * Updates distances for reuse candidates for all test suites. This should be run after evaluating.
 */
public class UpdateDistancesCommand extends AbstractCommand<UpdateDistancesArgs, Void> {

    private static final Logger logger = LoggerFactory.getLogger(UpdateDistancesCommand.class);

    private static Predicate<String> createRegexChecker(UpdateDistancesArgs args) {
        if (args.getMaxRegexLength().isEmpty()) {
            return (pattern) -> true;
        }

        int maxLength = args.getMaxRegexLength().getAsInt();
        return (pattern) -> {
            return pattern.length() < maxLength;
        };
    }

    private static BiPredicate<String, String> createRegexRelativeChecker(UpdateDistancesArgs args) {
        if (args.getMaxRegexDistance().isEmpty()) {
            return (l, r) -> true;
        }

        int maxDiff = args.getMaxRegexDistance().getAsInt();
        return (truth, candidate) -> {
            return Math.abs(truth.length() - candidate.length()) <= maxDiff;
        };
    }

    private final SQLiteConfig sqliteConfig;

    public UpdateDistancesCommand(RootArgs rootArgs, UpdateDistancesArgs args, SQLiteConfig sqliteConfig) {
        super(rootArgs, args);
        this.sqliteConfig = sqliteConfig;
    }

    @Override
    public Void call() throws Exception {
        String dbPath = String.format("jdbc:sqlite:%s", args.getDatabasePath());
        logger.info("connecting to database at {}", dbPath);
        Connection connection = DriverManager.getConnection(dbPath, this.sqliteConfig.toProperties());
        RegexDatabaseClient regexDatabaseClient = new RegexDatabaseClient(connection);
        logger.info("Successfully connected to database");

        UpdateDistancesService updateDistancesService = new UpdateDistancesService(regexDatabaseClient, createRegexChecker(args), createRegexRelativeChecker(args));

        logger.info("beginning to update distances...");
        updateDistancesService.computeAndInsertDistanceUpdateRecordsV3(args.computeAstDistances(), args.computeSemanticDistances());
        logger.info("finished to update distances");

        return null;
    }
}
