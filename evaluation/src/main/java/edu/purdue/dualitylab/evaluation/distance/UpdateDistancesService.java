package edu.purdue.dualitylab.evaluation.distance;

import dk.brics.automaton.Automaton;
import dk.brics.automaton.RegExp;
import edu.purdue.dualitylab.evaluation.db.RegexDatabaseClient;
import edu.purdue.dualitylab.evaluation.distance.ast.Tree;
import edu.purdue.dualitylab.evaluation.model.DistanceUpdateRecord;
import edu.purdue.dualitylab.evaluation.model.RawTestSuiteResultRow;
import edu.purdue.dualitylab.evaluation.util.BoundedCache;
import edu.purdue.dualitylab.evaluation.util.Pair;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.sql.SQLException;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;

public class UpdateDistancesService {

    private static final Logger logger = LoggerFactory.getLogger(UpdateDistancesService.class);

    private record DistanceInput(
            RawTestSuiteResultRow rawRow,
            Tree truthTree,
            Tree reuseTree
    ) {
    }

    private final RegexDatabaseClient databaseClient;
    private final DistanceMeasure<Automaton> automatonDistanceMeasure;
    private final BoundedCache<String, Optional<Tree>> treeCache;

    public UpdateDistancesService(RegexDatabaseClient regexDatabaseClient, DistanceMeasure<Automaton> automatonDistanceMeasure) {
        this.databaseClient = regexDatabaseClient;
        this.automatonDistanceMeasure = automatonDistanceMeasure;
        this.treeCache = new BoundedCache<>(100);
    }

    public void computeAndInsertDistanceUpdateRecordsV2() throws SQLException {
        // first, add the columns if needed
        logger.info("Adding distance columns to result table schema if needed");
        try {
            databaseClient.addDistanceColumnsToResults();
        } catch (SQLException e) {
            logger.warn("Error encountered while altering tables", e);
            logger.warn("continuing anyways...");
        }

        List<DistanceUpdateRecord> records = databaseClient.loadRawTestSuiteResultsForDistanceUpdate()
                .flatMap(row -> {
                    Optional<Tree> truthRegexTree = treeCache.get(row.truthRegex());
                    if (truthRegexTree == null) {
                        // the item has not been cached, so we need to build and store it
                        truthRegexTree = buildTree(row.truthRegex());
                        treeCache.put(row.truthRegex(), truthRegexTree);
                    }

                    // now that it has been built, we can interpret
                    if (truthRegexTree.isEmpty()) {
                        logger.warn("truth tree is empty for {}, so skipping row for test suite {}", row.truthRegexId(), row.testSuiteId());
                        // this pattern could not be built, so we should skip
                        return Optional.<DistanceInput>empty().stream();
                    }

                    Optional<Tree> candidateRegexTree = treeCache.get(row.candidateRegex());
                    if (candidateRegexTree == null) {
                        candidateRegexTree = buildTree(row.candidateRegex());
                        treeCache.put(row.candidateRegex(), candidateRegexTree);
                    }

                    if (candidateRegexTree.isEmpty()) {
                        logger.warn("candidate tree is empty for {}, so skipping row for test suite {}", row.candidateRegexId(), row.testSuiteId());
                        return Optional.<DistanceInput>empty().stream();
                    }

                    return Optional.of(new DistanceInput(row, truthRegexTree.get(), candidateRegexTree.get())).stream();
                })
                .map(input -> {
                    logger.info("computing distance between /{}/ and /{}/", input.rawRow().truthRegex(), input.rawRow().candidateRegex());
                    int astEditDistance = AstDistance.editDistance(input.truthTree(), input.reuseTree());

                    // TODO here we would also load up automaton stuff

                    return new DistanceUpdateRecord(input.rawRow().testSuiteId(), input.rawRow().candidateRegexId(), astEditDistance, Double.NaN);
                })
                .toList();

        databaseClient.updateManyTestSuiteResultsDistances(records);
        logger.info("finished computing all distance measurements");
    }

    public void computeAndInsertDistanceUpdateRecords() throws SQLException {
        // first, add the columns if needed
        logger.info("Adding distance columns to result table schema if needed");
        try {
            databaseClient.addDistanceColumnsToResults();
        } catch (SQLException e) {
            logger.warn("Error encountered while altering tables", e);
            logger.warn("continuing anyways...");
        }


        // next, compute the distances for everything
        logger.info("loading test suite result rows...");
        Map<Long, List<RawTestSuiteResultRow>> associatedGroups = databaseClient.loadRawTestSuiteResultsForDistanceUpdate()
                .collect(Collectors.groupingBy(RawTestSuiteResultRow::testSuiteId));

        logger.info("Starting to process distances...");
        for (Map.Entry<Long, List<RawTestSuiteResultRow>> entry : associatedGroups.entrySet()) {
            long testSuiteId = entry.getKey();
            String truthRegexPattern = entry.getValue().get(0).truthRegex();
            Optional<Tree> truthRegexTree = buildTree(truthRegexPattern);
            Optional<Automaton> truthAutomaton = buildAutomaton(truthRegexPattern);

            List<DistanceUpdateRecord> records = entry.getValue().stream()
                    .map(row -> {
                        Optional<Tree> candidateTree = buildTree(row.candidateRegex());
                        int astDistance = zipOptionals(truthRegexTree, candidateTree)
                                .map(treePair -> AstDistance.editDistance(treePair.a(), treePair.b()))
                                .orElse(-1);

                        double automatonDistance = zipOptionals(truthAutomaton, buildAutomaton(row.candidateRegex()))
                                .map(autoPair -> automatonDistanceMeasure.apply(autoPair.a(), autoPair.b()))
                                .orElse(Double.NaN);

                        return new DistanceUpdateRecord(testSuiteId, row.candidateRegexId(), astDistance, automatonDistance);
                    })
                    .toList();

            databaseClient.updateManyTestSuiteResultsDistances(records);
            logger.info("computed all distances for test suite {}", testSuiteId);
        }
    }

    private static Optional<Tree> buildTree(String pattern) {
        try {
            Tree truthRegexTree = AstDistance.buildTree(pattern);
            return Optional.of(truthRegexTree);
        } catch (IOException | OutOfMemoryError ignored) {
            // if we encounter one of these errors, then we should just skip edit distance
            logger.warn("failed to build tree for truth regex, so skipping AST measures for this test suite");
            return Optional.empty();
        }
    }

    private static Optional<Automaton> buildAutomaton(String pattern) {
        try {
            RegExp regExp = new RegExp(pattern, RegExp.NONE);
            Automaton auto = regExp.toAutomaton(true);
            return Optional.of(auto);
        } catch (IllegalArgumentException | StackOverflowError exe) {
            return Optional.empty();
        }
    }

    private static <T, U> Optional<Pair<T, U>> zipOptionals(Optional<T> first, Optional<U> second) {
        if (first.isPresent() && second.isPresent()) {
            return Optional.of(new Pair<>(first.get(), second.get()));
        } else {
            return Optional.empty();
        }
    }
}
