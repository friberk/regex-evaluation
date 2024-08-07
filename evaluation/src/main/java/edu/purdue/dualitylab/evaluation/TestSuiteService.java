package edu.purdue.dualitylab.evaluation;

import dk.brics.automaton.*;
import edu.purdue.dualitylab.evaluation.db.RawTestSuiteCollector;
import edu.purdue.dualitylab.evaluation.db.RegexDatabaseClient;
import edu.purdue.dualitylab.evaluation.model.*;
import edu.purdue.dualitylab.evaluation.safematch.SafeMatcher;
import edu.purdue.dualitylab.evaluation.util.CoverageUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.sql.SQLException;
import java.util.*;
import java.util.concurrent.ExecutorService;
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

    /**
     * Load existing regex test suites
     * @return Stream of regex test suites
     * @throws SQLException
     */
    public Stream<RegexTestSuite> loadRegexTestSuites() throws SQLException {
        return this.databaseClient.loadRawTestSuiteRows()
                .collect(new RawTestSuiteCollector())
                .stream();
    }

    public Stream<RegexTestSuite> createRegexTestSuitesFromRaw(int maxStringLength, ExecutorService safeMatchContext) throws SQLException {
        return createRegexTestSuitesFromRaw(maxStringLength, null, safeMatchContext);
    }

    public Stream<RegexTestSuite> createRegexTestSuitesFromRaw(int maxStringLength, TestSuiteStatistics stats, ExecutorService safeMatchContext) throws SQLException {
        return loadRawRegexTestSuites(maxStringLength).stream()
                .flatMap(rawSet -> expandTestSuite(rawSet, stats, safeMatchContext).stream());
    }

    public void updateTestSuiteCoverages() throws SQLException {
        Collection<RegexTestSuite> existingTestSuites = loadRegexTestSuites().toList();

        Map<Long, AutomatonCoverage> updatedCoverages = new HashMap<>();
        for (RegexTestSuite regexTestSuite : existingTestSuites) {
            // compile the automaton
            Optional<AutomatonCoverage> coverageOpt = CoverageUtils.createAutomatonCoverageOptional(regexTestSuite.pattern());
            if (coverageOpt.isEmpty()) {
                // skip this test suite if we can't actually get the coverage
                continue;
            }

            // evaluate coverage
            AutomatonCoverage coverage = coverageOpt.get();
            regexTestSuite.strings().stream()
                    .map(RegexTestSuiteString::subject)
                    .forEach(coverage::evaluate);

            updatedCoverages.put(regexTestSuite.id(), coverage);
        }

        // save all updated coverages
        databaseClient.updateManyTestSuiteCoverages(updatedCoverages);
    }

    private List<RegexStringSet> loadRawRegexTestSuites(int maxStringLength) throws SQLException {

        List<RegexStringSet> allRegexStringSets = new ArrayList<>();

        // first, group by project...
        var groupedByProjects = databaseClient.loadRawRegexTestSuites(maxStringLength)
                .collect(Collectors.groupingBy(RawRegexTestSuiteEntry::projectId));

        for (var projectEntry : groupedByProjects.entrySet()) {

            // ...then by regex...
            Map<Long, List<RawRegexTestSuiteEntry>> groupByRegexes = projectEntry.getValue().stream()
                    .collect(Collectors.groupingBy(RawRegexTestSuiteEntry::regexId));

            logger.info("project {} has {} test suites", projectEntry.getKey(), groupByRegexes.size());

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

    private Optional<RegexTestSuite> expandTestSuite(RegexStringSet stringSet, TestSuiteStatistics nullableStatistics, ExecutorService safeMatchContext) {
        Optional<TestSuiteStatistics> statistics = Optional.ofNullable(nullableStatistics);
        AutomatonCoverage coverage;
        Pattern pattern;
        statistics.ifPresent(TestSuiteStatistics::incrementTotalTestSuites);
        try {
            coverage = CoverageUtils.createAutomatonCoverage(stringSet.pattern());
        } catch (IllegalArgumentException exe) {
            // one of these failed to compile, so it is doomed :(
            statistics.ifPresent(TestSuiteStatistics::incrementBadSyntaxPatterns);
            return Optional.empty();
        } catch (DfaBudgetExceededException | StackOverflowError exe) {
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
            SafeMatcher matcher = new SafeMatcher(pattern, safeMatchContext);
            Optional<MatchStatus> status = MatchStatus.compute(matcher, example.subject());
            if (status.isEmpty()) {
                // if we got empty, then the pattern timed out while evaluating this string. We should drop the string,
                // and also consider removing the whole test suite
                continue;
            }

            strings.add(example.withMatchStatus(status.get()));
        }

        // if the test suite has no strings, then there's nothing to save
        if (strings.isEmpty()) {
            return Optional.empty();
        }

        return Optional.of(new RegexTestSuite(
                null,
                stringSet.projectId(),
                stringSet.regexId(),
                stringSet.pattern(),
                strings,
                coverage.getFullMatchVisitationInfoSummary(),
                coverage.getPartialMatchVisitationInfoSummary()
        ));
    }
}
