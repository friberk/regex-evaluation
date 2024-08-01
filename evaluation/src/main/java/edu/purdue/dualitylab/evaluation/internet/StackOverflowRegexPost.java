package edu.purdue.dualitylab.evaluation.internet;

import java.util.List;
import java.util.stream.Stream;

public record StackOverflowRegexPost(
        List<String> patterns,
        String type,
        String uri,
        List<String> uriAliases
) {
    public Stream<String> patternStream() {
        return patterns().stream();
    }
}
