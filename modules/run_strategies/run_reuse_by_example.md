# run_reuse_by_example

In order to query reuse-by-example for regex candidates, you need to refer back to the [evaluator](../evaluator/evaluation/src/main/java/edu/institution/lab/evaluation/commands/ManualQueryCommand.java) module. Carefully read the documentation of the `evaluator` module to get it running, otherwise, you will not be able to run the reuse-by-example strategy.

An example invocation is as follows:

```bash
cd evaluator
./gradlew :evaluation:run --args="manual-query --database <path to SQLite regex reuse database file)> --output <path to output NDJSON file for candidates> <path to file that contains test suites (i.e., regex composition bench)>"
```