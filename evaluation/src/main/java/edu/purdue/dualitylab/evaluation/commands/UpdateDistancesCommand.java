package edu.purdue.dualitylab.evaluation.commands;

import edu.purdue.dualitylab.evaluation.args.RootArgs;
import edu.purdue.dualitylab.evaluation.args.UpdateDistancesArgs;
import edu.purdue.dualitylab.evaluation.db.RegexDatabaseClient;
import edu.purdue.dualitylab.evaluation.distance.OverhangSizeDistance;
import edu.purdue.dualitylab.evaluation.distance.UpdateDistancesService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.sqlite.SQLiteConfig;

import java.sql.Connection;
import java.sql.DriverManager;

public class UpdateDistancesCommand extends AbstractCommand<UpdateDistancesArgs, Void> {

    private static final Logger logger = LoggerFactory.getLogger(UpdateDistancesCommand.class);

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

        UpdateDistancesService updateDistancesService = new UpdateDistancesService(regexDatabaseClient, new OverhangSizeDistance());

        logger.info("beginning to update distances...");
        updateDistancesService.computeAndInsertDistanceUpdateRecordsV2();
        logger.info("finished to update distances");

        return null;
    }
}
