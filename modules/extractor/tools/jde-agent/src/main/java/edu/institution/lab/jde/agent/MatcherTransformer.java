package edu.institution.lab.jde.agent;

import javassist.*;

import java.io.IOException;
import java.lang.instrument.ClassFileTransformer;
import java.lang.instrument.IllegalClassFormatException;
import java.security.ProtectionDomain;
import java.util.Optional;
import java.util.logging.Logger;
import java.util.regex.Matcher;

public class MatcherTransformer implements ClassFileTransformer {

    private final Logger logger;
    private final UsageLoggerTemplate usageLoggerTemplate;

    public MatcherTransformer(UsageLoggerTemplate usageLoggerTemplate) throws IOException {
        this.logger = Logger.getLogger("MatcherTransformer");
        this.usageLoggerTemplate = usageLoggerTemplate;
    }

    @Override
    public byte[] transform(ClassLoader loader,
                            String className,
                            Class<?> classBeingRedefined,
                            ProtectionDomain protectionDomain,
                            byte[] classfileBuffer) throws IllegalClassFormatException {

        if (!className.equals("java/util/regex/Matcher")) {
            return classfileBuffer;
        }

        logger.info(String.format("Transforming %s", className));

        CtClass patternClass;
        CtMethod matchesMethod;
        CtMethod findMethod;
        try {
            ClassPool pool = ClassPool.getDefault();
            pool.appendSystemPath();
            pool.importPackage("edu.institution.lab.jde.agent");
            pool.importPackage("com.fasterxml.jackson.databind");
            pool.importPackage("java.io");
            logger.info(String.format("Attempting to load class: %s", Matcher.class.getCanonicalName()));
            patternClass = pool.get(Matcher.class.getCanonicalName());
            logger.info("Loaded matcher class");
            matchesMethod = patternClass.getDeclaredMethod("matches");
            logger.info("Loaded matches method");
            findMethod = patternClass.getDeclaredMethod("find");
            logger.info("Loaded find method");
        } catch (NotFoundException e) {
            throw new RuntimeException(e);
        }

        logger.info("Starting to instrument the matcher method");

        try {
            instrumentFunction("Matcher#matches", matchesMethod);
            instrumentFunction("Matcher#find", findMethod);
            classfileBuffer = patternClass.toBytecode();
            logger.info("Successfully instrumented matcher methods");
            patternClass.detach();
        } catch (CannotCompileException e) {
            logger.severe(String.format("Error while instrumenting: %s", e.getMessage()));
            logger.severe(String.format("Reason: %s", e.getReason()));
        } catch (IOException e) {
            logger.severe(String.format("Error while instrumenting: %s", e.getMessage()));
        }

        return classfileBuffer;
    }

    private void instrumentFunction(String functionName, CtMethod method) throws IOException, CannotCompileException {
        Optional<String> code = usageLoggerTemplate.getInstrumentationCode(functionName);
        if (code.isPresent()) {
            method.insertBefore(code.get());
        }
    }
}
