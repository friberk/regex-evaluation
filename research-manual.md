# Research Manual

Here are some notes on common research tasks that I, Charlie, do. This list is not complete, but it's my best attempt.

## Data Collection

This section overviews of data collection tasks. This section describes some common files in use, what different tools do,
and how to use things.

### The Regex Database

One of the most important files in use for data collection is the regex database. This file is a SQLite database that contains
pretty much all raw data used in this project. I typically interact with this database using the `sqlite3` client, which is
the default client. You can use anything else, but that's the one that I typically use.

When opening this database, you can use `.schema` command to get documentation about _some_ of the tables included. The gist is:
* `project_spec` - this table contains metadata about all projects included. This table includes information about each project's
name, repository url, license, and more.
* `regex_entity` - this table contains all regexes we pulled from our data collection. Each record has a regular expression pattern
along with flags that say if this regex was statically and/or dynamically extracted.
* `regex_source_usage` - this table contains static use information for each regex. This table helps maintain a one-to-many relationship
between regex entities to where they occur in projects. Essentially, each record represents where a regex occurred in a project.
For example, there could be the row:

| regex_id | project_id | file | line | commit |
|----------|------------|------|------|--------|
| 10       | 100 | path/to/file | 100 | 1023412401204 |

which suggests that the pattern for regex 10 occurs in project 100 at /path/to/file at line 100 for commit hash. This table can be used
to find information about:
* Which regexes occur in a project
* which regexes occur in mulitple projects
* How many regexes are found in a project

and other information.

* `regex_subject` - this table contains dynamic extraction information. Similarly to `regex_source_usage`, this table contains records
on which input strings were evaluated on which regexes in each project. Additionally, each record shows if the subject matched or not
and which regex function was used. This table is used to figure out test suites.

* `test_suite` - this table represents specific test suites. Each test suite is a regex and a collection of strings evaluated on that
regex. These actual strings are found in `test_suite_string`. Each test suite record has a regex, the project that this test suite
originated from, and coverage information.

* `test_suite_string` - this table is the many-to-one relationship of strings for each test suite. Each record has the subject strings and
coverage information.

* `test_suite_result` - A test suite result record is another regexes from a different project that matches against the provided test_suite.
Each record also has information on matching, relative coverage, and distances.


Practically all operations will use this database in some way. Typically, I try to write tools to automate interactions with the database.

Likewise, this file is _really, really big_. You should only interact with this file in either a very large storage medium or on one of the
lab server machines. If you store it on a lab server, you should make sure it is stored in a scratch directory (i.e., not your home drive).

### Apptainer

[Apptainer](https://apptainer.org/) is a container runtime available on our geography cluster. It's compatible with docker containers. I recommend that you do most
of your work on one of the geography cluster machines.

#### Environment Configuration
You must add the following environment variables to your `.bashrc` file (or wahtever configuration files you use):
```shell
export APPTAINER_TMPDIR=/local/scratch/a/<your username>/.apptainer-tmp
export APPTAINER_CACHEDIR=/local/scratch/a/<your username>/.apptainer-cache
```
You might need to use those files. These variables use bulk scratch storage for building images, which is fairly disk intensive.

#### Buliding Images
Another common task is building new apptainer containers from docker containers. An example is:
```shell
$ apptainer build regex-extractor.sif docker://softwaresale/regex-extractor:3.5.1
```
In this example, I build a container called `regex-extractor.sif` from the docker container specified at my registry. Swap those
values out depending on 

#### Executing a Conatiner Image
Running an image can be a bit tricky sometimes. A quick and dirty example is:
```shell
$ apptainer run --bind `realpath .`:`realpath .` ~/regex-extractor.sif ARGS...
```
The only interesting thing here is the `--bind` argument. Essentially, apptainer allows you to seamlessly interact with your host filesystem from the guest.
However, when working in your scratch drive, you need to use bind to tell the conatiner to mount that directory into your container. Read more about
apptainer run [here](https://apptainer.org/docs/user/main/cli/apptainer_run.html).

### The Static Extractor
The static extractor's purpose is for fetching packages, extracting regexes and examples from projects, and more. There are some additional
features like creating reports. There are additional features, but those probably shouldn't be used.

The repository is located [here](https://github.com/PurdueDualityLab/regex-extractor-v2). There is a decent amount of code-level documentation
along with read me files scattered throughout. This project is almost entirely written in Rust, along with some language-specific static extractor
servers. Ideally, not much needs to be changed about this project. If you need further clarifications about the architecture of the system,
feel free to consult me.

If you do not need to make any modifications, you can use my pre-built containerized build [at my dockerhub account](https://hub.docker.com/repository/docker/softwaresale/regex-extractor/general).
Just use the latest version.

Ideally, you shouldn't need to use this tool much because most of our data is collected. Feel free to reach out if you end up needing to collect
something.

### The Evaluator
The evaluator tool is much less robust. It has a few hodge-podge uses. Mainly, it's purpose is
- figuring out test suites
- finding resuse candidates
- measuring distances between candidates and truth regexes
- measuring test suite coverage
- interacting with internet regexes

The source is [here](https://github.com/PurdueDualityLab/regex-evaluation) and a pre-built container is [here](https://hub.docker.com/repository/docker/softwaresale/regex-evaluator/general).
It is written in Java. Like the static extractor, there is a lot of code-level documentation and Readme files. Please read those.

#### Evaluator Setup
1. Make sure that you read the [SQLite Extensions Section](https://github.com/PurdueDualityLab/regex-evaluation/tree/main#sqlite-extensions-dependency) of the readme. I have written some
SQLite extensions to make writing queries easier and more consistent.
2. I'll assume that you have a containerized version of this tool in your home directory.

#### Common Use-Case: Pulling Test Suites

```shell
apptainer run --bind `realpath .`:`realpath .` ~/regex-evaluator.sif --temp-files-memory pull-test-suites regexes-combined-300k.sqlite
```

This command will take all subject strings in the database and create test suites out of them.

#### Common Use-Case: Finding Reuse Candidates
```shell
apptainer run --bind `realpath .`:`realpath .` ~/regex-evaluator.sif --temp-files-memory evaluate regexes-combined-300k.sqlite
```

This command assumes that there are test suites in the database. This will find reuse candidates for all test suites and store
them all in the database.

#### Common Use-Case: Updating Distances
```shell
apptainer run --bind `realpath .`:`realpath .` ~/regex-evaluator.sif --temp-files-memory update-distances regexes-combined-300k.sqlite
```
This command goes through all existing test suites and computes the distances between truth and candidates.

## Some Stuff You'll Probably Have To Do

Here's my guidance on future tasks that'll have to happen.

### Debug AST/Semantic Distance Stuff
There is support for computing AST distance as well as semantic distance. These tools exist, but they seem to be a bit buggy. AST distance implementation is found
[here](https://github.com/PurdueDualityLab/regex-evaluation/tree/main/evaluation/src/main/java/edu/purdue/dualitylab/evaluation/distance), and semantic distance is found
[mostly here](https://github.com/PurdueDualityLab/dk.brics.automaton/blob/master/src/main/java/dk/brics/automaton/GenerateStrings.java). Ethan did a lot on this,
so feel free to ask him questions.

You can run these distance measures to see what I mean. It's hard to get them to run all the way through.

### Extending Evaluator to support partial accuracy
This feature allows us to call a regex a reuse candidate if it matches 90% of strings. I have an implementation [here](https://github.com/PurdueDualityLab/regex-evaluation/pull/2).
It'll probably take some additional testing though.

### Compute Distances of Synthesized Regexes
There are numerous files generated by Nate that hold synthesized regexes. There should be documentation somewhere of how those files are formatting.
Currently, there is no way to load those files into our evaluation tool. There are two options:
1) extend the evaluation tool to read those files
2) transfer Nate's synthesized data into the regex database.

It's your call either way. 2 might be easier, though.
