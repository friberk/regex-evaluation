package edu.purdue.dualitylab.evaluation;

import dk.brics.automaton.*;
import edu.purdue.dualitylab.evaluation.db.RegexDatabaseClient;
import edu.purdue.dualitylab.evaluation.model.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.sql.SQLException;
import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.regex.PatternSyntaxException;
import java.util.stream.Collectors;
import java.util.stream.Stream;

public final class TestSuiteService {

    private static final Logger logger = LoggerFactory.getLogger(TestSuiteService.class);

    private final RegexDatabaseClient databaseClient;

    public TestSuiteService(RegexDatabaseClient databaseClient) {
        this.databaseClient = databaseClient;
    }

    public Stream<RegexTestSuite> loadRegexTestSuites() throws SQLException {
        return loadRegexTestSuites(null);
    }

    public Stream<RegexTestSuite> loadRegexTestSuites(TestSuiteStatistics stats) throws SQLException {
        return loadRawRegexTestSuites().stream()
                .flatMap(rawSet -> expandTestSuite(rawSet, stats).stream());
    }

    private List<RegexStringSet> loadRawRegexTestSuites() throws SQLException {

        List<RegexStringSet> allRegexStringSets = new ArrayList<>();

        // first, group by project...
        var groupedByProjects = databaseClient.loadRawRegexTestSuites()
                .collect(Collectors.groupingBy(RawRegexTestSuiteEntry::projectId));

        for (var projectEntry : groupedByProjects.entrySet()) {

            // ...then by regex...
            Map<Long, List<RawRegexTestSuiteEntry>> groupByRegexes = projectEntry.getValue().stream()
                    .collect(Collectors.groupingBy(RawRegexTestSuiteEntry::regexId));

            for (var regexEntry : groupByRegexes.entrySet()) {
                // ... and finally combine everything together
                List<RawRegexTestSuiteEntry> testSuiteComponents = regexEntry.getValue();

                // all these entities are from the same regex in the same project
                RawRegexTestSuiteEntry metadataEntry = testSuiteComponents.stream().findFirst().orElseThrow();
                String pattern = metadataEntry.pattern();
                long regexId = metadataEntry.regexId();
                long projectId = metadataEntry.projectId();

                var strings = testSuiteComponents.stream().map(RegexTestSuiteString::fromRaw).collect(Collectors.toSet());
                allRegexStringSets.add(new RegexStringSet(regexId, projectId, pattern, strings));
            }
        }

        return allRegexStringSets;
    }

    private Optional<RegexTestSuite> expandTestSuite(RegexStringSet stringSet, TestSuiteStatistics nullableStatistics) {
        Optional<TestSuiteStatistics> statistics = Optional.ofNullable(nullableStatistics);
        AutomatonCoverage coverage;
        Pattern pattern;
        statistics.ifPresent(TestSuiteStatistics::incrementTotalTestSuites);
        try {
            logger.info("Starting to compile automaton for pattern /{}/...", stringSet.pattern());
            RegExp regExp = new RegExp(stringSet.pattern(), RegExp.NONE);
            Automaton auto = regExp.toAutomaton();
            logger.info("determinizing...");
            auto.determinize();
            logger.info("minimizing...");
            auto.minimize();
            logger.info("Beginning to create coverage automaton for automaton with {} states and {} transitions", auto.getNumberOfStates(), auto.getNumberOfTransitions());
            coverage = new AutomatonCoverage(auto);
            logger.info("Successfully compiled");
        } catch (IllegalArgumentException exe) {
            logger.warn("Failed to compile automaton /{}/: {}", stringSet.pattern(), exe.getMessage());
            // one of these failed to compile, so it is doomed :(
            statistics.ifPresent(TestSuiteStatistics::incrementBadSyntaxPatterns);
            return Optional.empty();
        } catch (DfaBudgetExceededException exe) {
            logger.warn("DFA budget exceeded for pattern /{}/: {}", stringSet.pattern(), exe.getMessage());
            statistics.ifPresent(TestSuiteStatistics::incrementDFABudgetExceeded);
            return Optional.empty();
        }

        try {
            pattern = Pattern.compile(stringSet.pattern());
        } catch (PatternSyntaxException pse) {
            logger.warn("Failed to compile pattern /{}/: {} - {}", pse.getPattern(), pse.getMessage(), pse.getDescription());
            statistics.ifPresent(TestSuiteStatistics::incrementBadSyntaxPatterns);
            return Optional.empty();
        }

        Set<RegexTestSuiteString> strings = new HashSet<>();
        for (RegexTestSuiteString example : stringSet.strings()) {
            coverage.evaluate(example.subject());
            Matcher matcher = pattern.matcher(example.subject());
            MatchStatus status = MatchStatus.compute(matcher);
            strings.add(example.withMatchStatus(status));
        }

        // get coverage info
        AutomatonCoverage.VisitationInfoSummary visitationInfo = coverage.getVisitationInfoSummary();

        return Optional.of(new RegexTestSuite(stringSet.projectId(), stringSet.regexId(), stringSet.pattern(), strings, visitationInfo));
    }
}
