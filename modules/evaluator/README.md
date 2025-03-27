
# Regex Evaluation

This repository provides tools for performing the actual evaluation of the regex reuse project. This includes tasks
such as:
- Categorize test suite strings as matching or mismatching
- Finding reuse candidates for test suites
- Compute AST/semantic distance measures
- Create database of internet regexes and evaluate them

As a side note, this project depends heavily on [our fork of the brics library](./dk.brics.automaton/README.md).
This package is where e-similarity and automaton coverage are implemented. If you need to update the implementation of
either of these tools, update it upstream and then update the submodule in this project.

## Using
The best way to use the evaluation tool is to use it as a container. gradle handles building a container for you.
Simply run the `:evaluation:dockerBuildImage` task to build a containerized version of this application.

Otherwise, you can use the `gradle run` task to execute the main application. See the `--help` flag to get info on how
to use the command line interface.

To build, use gradle. A gradle wrapper is provided so you do not have to install gradle on your machine.

Running `./gradlew assemble` will compile the entire project.

### SQLite Extensions Dependency
Some of the queries use the same SQLite extensions used by the extractor. The extractor repository has a package that
provides these extensions in a shared library. That package is located [here](../extractor/tools/sqlite-regex-extensions/Cargo.toml).
Take that repository, build it, and find the shared library it produces (it should be called libsqlite-regex-extensions.so
or something like that.) As mentioned in the help docs, set the `SQLITE_REGEX_EXTENSION_PATH=<whatever the absolute path to that library is>`.
Do this each time you execute the evaluator. Alternatively, you can set that path as a flag, but I find the environment
variable approach easier to use.

## Source Map
- There is a brics submodule. Make sure that is fetched before building
- evaluation holds all relevant code.