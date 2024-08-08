package edu.purdue.dualitylab.evaluation.internet;

import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.stream.Stream;

public record StackOverflowRegexPost(
        List<String> patterns,
        String type,
        String uri,
        List<String> uriAliases
) {
    public static final int STACK_OVERFLOW_ORIGIN_ID = 1;

    public Stream<String> patternStream() {
        return patterns().stream();
    }

    public StackOverflowRegexPost withPatterns(Collection<String> newPatterns) {
        return new StackOverflowRegexPost(new ArrayList<>(newPatterns), this.type, this.uri, this.uriAliases);
    }
}
