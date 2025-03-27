package edu.institution.lab.jde.agent;

import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.logging.Logger;

public class UsageLogger {
    private static final Logger logger = Logger.getLogger(UsageLogger.class.getName());
    private static UsageLogger instance = null;

    public static void init() {
        instance = new UsageLogger();
    }

    public static void tryLogUsage(UsageRecord record, String fileName) {
        if (instance == null) {
            logger.warning("Singleton instance is null, so NOP");
            return;
        }

        try {
            instance.logUsage(record, fileName);
        } catch (IOException e) {
            logger.warning(String.format("error while trying to log usage record: %s", e.getMessage()));
        }
    }

    private final ObjectMapper mapper;

    private UsageLogger() {
        mapper = new ObjectMapper();
    }

    private void logUsage(UsageRecord record, String fileName) throws IOException {
        FileWriter fileWriter = new FileWriter(fileName, true);
        BufferedWriter writer = new BufferedWriter(fileWriter);
        PrintWriter pw = new java.io.PrintWriter(writer);
        mapper.writeValue(pw, record);
    }
}
