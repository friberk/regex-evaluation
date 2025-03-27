package parsers.java;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Represents an extracted regex
 */
public class RegexObject {
    private final String pattern;

    private final String flags;

    private final long lineNo;

    private String sourceFile;

    public RegexObject(String pattern, String flags, long lineNo, String sourceFile) {
        this.pattern = pattern;
        this.flags = flags;
        this.lineNo = lineNo;
        this.sourceFile = sourceFile;
    }

    @Override
    public String toString() {
        return "RegexObject{" +
                "pattern='" + pattern + '\'' +
                ", flags='" + flags + '\'' +
                ", lineNo=" + lineNo +
                ", sourceFile='" + sourceFile + '\'' +
                '}';
    }

    public String getPattern() {
        return pattern;
    }

    public String getFlags() {
        return flags;
    }

    public long getLineNo() {
        return lineNo;
    }

    public String getSourceFile() {
        return sourceFile;
    }

    public void setSourceFile(String file) {
        this.sourceFile = file;
    }
}
