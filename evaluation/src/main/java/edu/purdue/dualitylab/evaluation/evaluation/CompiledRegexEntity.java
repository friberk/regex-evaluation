package edu.purdue.dualitylab.evaluation.evaluation;

import edu.purdue.dualitylab.evaluation.model.CandidateRegex;

import java.util.Optional;
import java.util.regex.Pattern;
import java.util.regex.PatternSyntaxException;

public record CompiledRegexEntity(
        long id,
        long projectId,
        Pattern regexPattern
) {

    /**
     * Try to compile a regex entity into a regex. Return empty optional if regex cannot be compiled
     * @param regex candidate regex to try to compile
     * @return Filled optional if valid, or empty if there is a syntax error
     */
    public static Optional<CompiledRegexEntity> tryCompile(CandidateRegex regex) {
        try {
            Pattern regexEntityPattern = Pattern.compile(regex.pattern());
            return Optional.of(new CompiledRegexEntity(regex.id(), regex.projectId(), regexEntityPattern));
        } catch (PatternSyntaxException | StackOverflowError exe) {
            return Optional.empty();
        }
    }
}