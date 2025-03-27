package edu.institution.lab.jde.agent;

import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.File;
import java.io.IOException;
import java.lang.instrument.Instrumentation;
import java.net.URISyntaxException;
import java.net.URL;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.jar.JarFile;
import java.util.logging.Logger;
import java.util.regex.Matcher;

public class JavaDynamicRegexExtractorAgent {

    private static final Logger logger = Logger.getLogger(JavaDynamicRegexExtractorAgent.class.getName());

    // premain static loader
    public static void premain(String agentArgs, Instrumentation inst) {
        logger.info("Successfully statically loaded");

        MatcherTransformer matcherTransformer;
        try {
            UsageLoggerTemplate template = UsageLoggerTemplate.initFromEnv();
            matcherTransformer = new MatcherTransformer(template);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        inst.addTransformer(matcherTransformer, true);

        logger.info(String.format("pattern class info: %s", Matcher.class.getName()));

        UsageLogger.init();

        try {
            inst.retransformClasses(Matcher.class);
        } catch (Exception ex) {
            logger.severe(String.format("Error while transforming matcher class: %s", ex.getMessage()));
        }

        try {
            JarFile openMapperJar = findJarFile(ObjectMapper.class);
            inst.appendToSystemClassLoaderSearch(openMapperJar);
            JarFile usageRecordJar = findJarFile(UsageRecord.class);
            inst.appendToSystemClassLoaderSearch(usageRecordJar);
            inst.appendToBootstrapClassLoaderSearch(usageRecordJar);
        } catch (Exception exe) {
            throw new RuntimeException(exe);
        }
    }

    private static JarFile findJarFile(Class<?> clazz) throws URISyntaxException, IOException {
        URL jarURL = clazz.getProtectionDomain().getCodeSource().getLocation();
        logger.info(String.format("Found %s jar at %s", clazz.getSimpleName(), jarURL.toString()));
        Path jarFilePath = Paths.get(jarURL.toURI());
        File potentialJarFile = jarFilePath.toFile();
        return new JarFile(potentialJarFile);
    }
}
