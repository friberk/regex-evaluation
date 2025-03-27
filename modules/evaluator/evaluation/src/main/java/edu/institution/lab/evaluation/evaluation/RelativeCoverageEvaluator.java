package edu.institution.lab.evaluation.evaluation;

import dk.brics.automaton.Automaton;
import dk.brics.automaton.AutomatonCoverage;
import edu.institution.lab.evaluation.model.RawTestSuiteResultRow;
import edu.institution.lab.evaluation.model.RegexTestSuite;
import edu.institution.lab.evaluation.model.RegexTestSuiteString;
import edu.institution.lab.evaluation.model.RelativeCoverageUpdate;

import java.util.Collection;
import java.util.concurrent.Callable;

public class RelativeCoverageEvaluator implements Callable<RelativeCoverageUpdate> {

    private final RegexTestSuite testSuite;
    private final RawTestSuiteResultRow candidateRow;
    private final AutomatonCoverage candidateCoverage;

    public RelativeCoverageEvaluator(RegexTestSuite testSuite, RawTestSuiteResultRow candidateRow, Automaton candidateAutomaton) {
        this.testSuite = testSuite;
        this.candidateRow = candidateRow;
        this.candidateCoverage = new AutomatonCoverage(candidateAutomaton);
    }

    @Override
    public RelativeCoverageUpdate call() throws Exception {
        testSuite.strings().stream()
                .map(RegexTestSuiteString::subject)
                .forEach(candidateCoverage::evaluate);

        return new RelativeCoverageUpdate(testSuite.id(), candidateRow.candidateRegexId(), candidateCoverage);
    }
}
