package edu.purdue.dualitylab.evaluation.internet;

import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class RegexFixer {

    private static final Pattern tailingSlashDetector = Pattern.compile("/[dgimsuvy]*$");
    private static final Pattern javaCallExtractor = Pattern.compile("Pattern\\.compile\\(\"([^\"]+)\"\\)");
    private static final Pattern pythonCallExtractor = Pattern.compile("re\\.compile\\s*\\([^'\"]*['\"]([^'\"]+)['\"][^)]*\\)\\s*$");

    public static String fixInternetRegex(String pattern) {

        // Fix up slashes
        if (pattern.charAt(0) == '/') {
            Matcher matcher = tailingSlashDetector.matcher(pattern);
            boolean matches = matcher.find();
            if (matches) {
                int innerRegexEnd = matcher.start();
                pattern = pattern.substring(0, innerRegexEnd);
            }
        } else if (pattern.startsWith("Pattern.compile")) {
            // Java regex. Extract pattern from call
            Matcher matcher = javaCallExtractor.matcher(pattern);
            boolean matches = matcher.find();
            if (matches) {
                pattern = matcher.group(1);
            }
        } else if (pattern.startsWith("re.compile")) {
            Matcher matcher = pythonCallExtractor.matcher(pattern);
            boolean matches = matcher.find();
            if (matches) {
                pattern = matcher.group(1);
            }
        }

        return pattern;
    }
}
