package edu.purdue.dualitylab.evaluation.evaluation;

import edu.purdue.dualitylab.evaluation.model.CandidateRegex;

import java.util.Optional;
import java.util.regex.Pattern;
import java.util.regex.PatternSyntaxException;

public record CompiledRegexEntity(
        long id,
        Pattern regexPattern
) {

    /**
     * Try to compile a regex entity into a regex. Return empty optional if regex cannot be compiled
     * @param id Regex Entity Id
     * @param pattern Regex entity pattern
     * @return Filled optional if valid, or empty if there is a syntax error
     */
    public static Optional<CompiledRegexEntity> tryCompile(long id, String pattern) {
        try {
            Pattern regexEntityPattern = Pattern.compile(pattern);
            return Optional.of(new CompiledRegexEntity(id, regexEntityPattern));
        } catch (PatternSyntaxException | StackOverflowError exe) {
            return Optional.empty();
        }
    }

    public static Optional<CompiledRegexEntity> tryCompile(CandidateRegex regex) {
        return tryCompile(regex.id(), regex.pattern());
    }
}