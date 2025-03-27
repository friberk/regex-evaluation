package edu.institution.lab.evaluation.args;

import com.beust.jcommander.Parameter;
import com.beust.jcommander.ParameterException;
import com.beust.jcommander.Parameters;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Objects;

@Parameters(commandDescription = "Perform internet regex evaluation")
public class InternetRegexesArgs {

    private static final Logger logger = LoggerFactory.getLogger(InternetRegexesArgs.class);

    @Parameter(description = "Static extraction results database file", required = true)
    private String regexDatabaseFile;

    @Parameter(names = {"-u", "--update-only"}, description = "Only compute updates")
    private Boolean updateOnly;

    @Parameter(names = {"-f", "--internet-file"}, description = "NDJSON file containing StackOverflow regex posts")
    private String internetPostsFile;
    @Parameter(names = {"-d", "--internet-db"}, description = "SQLite database containing internet regexes", required = true)
    private String internetDb;

    /**
     * Assess if the user is trying to load posts from an NDJson file and save them to a SQLite file.
     * @return True if doing the thing
     */
    public boolean isLoadPostsFromFileAndSaveToDb() {
        return internetPostsFile != null;
    }

    /**
     * If true, then we are using a sqlite database as our input
     * @return true if using internet regexes database
     */
    public boolean isInternetRegexesDBInput() {
        return internetPostsFile == null;
    }

    /**
     * If true, then no database is used at all. read candidates from file and perform evaluation
     * @return True
     */
    public boolean isReadInputFromFileOnly() {
        return internetPostsFile != null && internetDb == null;
    }

    /**
     * Path to the standard regex database
     * @return
     */
    public String getRegexDatabasePath() {
        return regexDatabaseFile;
    }

    /**
     * Path to regex database to read from
     * @return
     */
    public String getInternetRegexDatabasePath() {
        return internetDb;
    }

    public String getStackOverflowPostsFilePath() {
        return internetPostsFile;
    }

    public boolean isUpdatesOnly() {
        return Objects.requireNonNullElse(updateOnly, false);
    }
}
