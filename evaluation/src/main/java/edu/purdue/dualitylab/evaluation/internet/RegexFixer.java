package edu.purdue.dualitylab.evaluation.internet;

import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class RegexFixer {

    private static final Pattern tailingSlashDetector = Pattern.compile("/[dgimsuvy]*$");
    private static final Pattern functionCallDetector = Pattern.compile("^[\\w.]+\\(.+\\)$");

    public static String fixInternetRegex(String pattern) {

        // Fix up slashes
        if (pattern.charAt(0) == '/') {
            Matcher matcher = tailingSlashDetector.matcher(pattern);
            boolean matches = matcher.find();
            if (matches) {
                int innerRegexEnd = matcher.start();
                pattern = pattern.substring(0, innerRegexEnd);
            }
        }

        return pattern;
    }
}
