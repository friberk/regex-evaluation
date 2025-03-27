package edu.institution.lab.evaluation.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonAlias;
import java.util.Optional;

public record TestString(
    @JsonProperty("string_id")
    @JsonAlias("stringId")
    Optional<Long> stringId,

    @JsonProperty("string")
    String string,

    @JsonProperty("full_match")
    @JsonAlias("fullMatch")
    boolean fullMatch,

    @JsonProperty("partial_match")
    @JsonAlias("partialMatch")
    boolean partialMatch,

    @JsonProperty("first_sub_match_start")
    @JsonAlias("firstSubMatchStart")
    Optional<Integer> firstSubMatchStart,

    @JsonProperty("first_sub_match_end")
    @JsonAlias("firstSubMatchEnd")
    Optional<Integer> firstSubMatchEnd,

    @JsonProperty("matched_string")
    @JsonAlias("matchedString")
    String matchedString
) {
    // Convert numeric boolean (0/1) to Java boolean
    public static TestString fromJson(Optional<Long> id, String str, int fullMatch, int partialMatch,
                                     Optional<Integer> start, Optional<Integer> end, String matched) {
        return new TestString(id, str, fullMatch == 1, partialMatch == 1, start, end, matched);
    }
}
