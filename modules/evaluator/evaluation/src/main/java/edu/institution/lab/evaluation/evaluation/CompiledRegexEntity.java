package edu.institution.lab.evaluation.evaluation;

import edu.institution.lab.evaluation.model.CandidateRegex;

import java.util.Optional;
import java.util.regex.Pattern;
import java.util.regex.PatternSyntaxException;

/**
 * Represents a compiled regex entity. We keep the regex and project id, and also keep the compiled Pattern for the
 * pattern.
 * @param id The regex's unique id
 * @param projectId The project that originated this regex
 * @param regexPattern The compiled regex.
 */
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