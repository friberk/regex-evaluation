package edu.institution.lab.jde.agent;

import java.io.*;
import java.util.Optional;

public final class UsageLoggerTemplate {

    private final String template;
    private final String outputPath;

    public static UsageLoggerTemplate initFromEnv() throws IOException {
        String propertyValue = System.getProperty("edu.institution.lab.jde.agent.exampleOutputPath");
        String envValue = System.getenv("DYN_EXTRACTOR_OUTPUT_PATH");
        String finalValue = null;
        if (propertyValue != null) {
            finalValue = propertyValue;
        } else if (envValue != null) {
            finalValue = envValue;
        }

        return new UsageLoggerTemplate(finalValue);
    }

    private UsageLoggerTemplate(String outputPath) throws IOException {
        InputStream resourceStream = getClass().getClassLoader().getResourceAsStream("logUsageTemplateMatcherRaw.java");
        if (resourceStream == null) {
            throw new RuntimeException("Could not find resource 'logUsageTemplateMatcherRaw.java'.");
        }
        BufferedReader reader = new BufferedReader(new InputStreamReader(resourceStream));
        StringWriter templateStringWriter = new StringWriter();
        reader.transferTo(templateStringWriter);


        template = templateStringWriter.toString();
        this.outputPath = outputPath;

        resourceStream.close();
    }

    public Optional<String> getInstrumentationCode(String functionName) {
        if (outputPath == null) {
            return Optional.empty();
        }

        String code = getInstrumentationCode(this.outputPath, functionName);
        return Optional.of(code);
    }

    public String getInstrumentationCode(String outputPath, String functionName) {
        return String.format(template, functionName, outputPath);
    }
}
