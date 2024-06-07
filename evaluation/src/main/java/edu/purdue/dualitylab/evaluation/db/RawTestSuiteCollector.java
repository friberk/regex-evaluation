package edu.purdue.dualitylab.evaluation.db;

import edu.purdue.dualitylab.evaluation.model.RawTestSuiteRow;
import edu.purdue.dualitylab.evaluation.model.RegexTestSuite;
import edu.purdue.dualitylab.evaluation.model.RegexTestSuiteString;

import java.util.*;
import java.util.function.BiConsumer;
import java.util.function.BinaryOperator;
import java.util.function.Function;
import java.util.function.Supplier;
import java.util.stream.Collector;
import java.util.stream.Collectors;

public class RawTestSuiteCollector implements Collector<RawTestSuiteRow, HashMap<Long, List<RawTestSuiteRow>>, List<RegexTestSuite>> {
    @Override
    public Supplier<HashMap<Long, List<RawTestSuiteRow>>> supplier() {
        return HashMap::new;
    }

    @Override
    public BiConsumer<HashMap<Long, List<RawTestSuiteRow>>, RawTestSuiteRow> accumulator() {
        return (associated, item) -> {
            if (associated.containsKey(item.testSuiteId())) {
                associated.get(item.testSuiteId()).add(item);
            } else {
                List<RawTestSuiteRow> list = new ArrayList<>();
                list.add(item);
                associated.put(item.testSuiteId(), list);
            }
        };
    }

    @Override
    public BinaryOperator<HashMap<Long, List<RawTestSuiteRow>>> combiner() {
        return (left, right) -> {
            right.forEach((rightKey, rightValue) -> {
                left.merge(rightKey, rightValue, (mergeLeft, mergeRight) -> {
                    mergeLeft.addAll(mergeRight);
                    return mergeLeft;
                });
            });

            return left;
        };
    }

    @Override
    public Function<HashMap<Long, List<RawTestSuiteRow>>, List<RegexTestSuite>> finisher() {
        return (associated) -> {
            List<RegexTestSuite> testSuites = new ArrayList<>();
            for (Map.Entry<Long, List<RawTestSuiteRow>> entry : associated.entrySet()) {
                long testSuiteId = entry.getKey();
                List<RawTestSuiteRow> testSuiteRows = entry.getValue();
                if (testSuiteRows.isEmpty()) {
                    throw new RuntimeException("Test suite rows should never be empty");
                }
                // there should be at least
                RawTestSuiteRow metaDataRow = testSuiteRows.get(0);

                Set<RegexTestSuiteString> strings = testSuiteRows.stream()
                                .map(RawTestSuiteRow::testSuiteString)
                                .collect(Collectors.toSet());

                testSuites.add(new RegexTestSuite(
                        testSuiteId,
                        metaDataRow.projectId(),
                        metaDataRow.regexId(),
                        metaDataRow.pattern(),
                        strings,
                        metaDataRow.fullCoverageSummary(),
                        metaDataRow.partialCoverageSummary()
                ));
            }

            return testSuites;
        };
    }

    @Override
    public Set<Characteristics> characteristics() {
        return Set.of();
    }
}
