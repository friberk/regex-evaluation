
# Regex Extractor

## Overview

The extractor runs all of the steps at once:
1. user starts whole process, which involves:
- cloning the repository
- performing static extraction
- performing dynamic extraction (if necessary/possible)
- combining all results
- cleaning up

As you can tell, the old extractor required each step to be run in series by the user, while the new one automates the entire process.
This new system also provides a few benefits from the old one:
1. better reporting/traceability in the system. We can tell exactly what happened to every package we process along that processing pipeline.
2. fewer false positives. 
more

## Using this project
To use this project, it is recommended to build a docker image:
`$ docker build -t extractor .`

Currenty, a build is available at [here](https://hub.docker.com/r/anonymous/regex-extractor).

## Code Map
This project is written in Rust and uses Cargo for package management.

- `driver/` - this package builds the driver binary program. It is the user interface to the extraction pipeline. It implements each command that the user can
perform.
- `shared/` - this package produces a library of reusable code shared by all projects. This library provides utilities like models and repository utilities
- `static-extraction/` -  package contains code related to performing static extraction. This is consumed by the driver to implement the extraction pipeline.
- `dynamic-extraction/` - contains code for implementing dynamic extraction pipeline
- `db/` - code for interacting with SQLite databases. All intermediate files are SQLite databases. This package contains code for interfacing with those.
- `reporting/` - automatically generate reports for data regarding a regex database.
- `evaluation/` - old version of [this](../evaluator/README.md) module.
- `tools/` - holds 3rd party static extractor servers and more.

## Setting Up
- Getting `tools/` setup. See [README.md](./tools/README.md) in that directory
- Build project using cargo `cargo build --release`
- use `extract` command to perform data collection

