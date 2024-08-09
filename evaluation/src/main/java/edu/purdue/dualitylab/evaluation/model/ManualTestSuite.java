package edu.purdue.dualitylab.evaluation.model;

import java.util.List;

public record ManualTestSuite(
        List<String> positiveStrings,
        List<String> negativeStrings
) {
}
