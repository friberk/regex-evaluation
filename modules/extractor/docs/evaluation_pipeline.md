
# Evaluation Pipeline

Here is an overview of the steps taken to perform the evaluation

### Ecosystem Dump Generation -- `driver ecosystem-dump`
First, the evaluation pipeline requires a large corpus of package specs to inspect.
We get these from ecosystems. The lab has a dump saved on *Tokyo*. This tool must be
run on *tokyo* to work. **If possible, get a dump file from someone else**.

### Raw data extraction -- `driver extract`

| Takes as input | Produces                  |
|----------------|---------------------------|
| PackageSpecs[] | Regex Info Database       |
|                | Package processing report |

This phase takes in a set of packages and produces a database of data collected from
the extraction process as well as a report on what happened to each package. This
phase extracts the following information:
- A corpus of statically extracted regexes
- Information on where these statically extracted regexes occur in source (may occur across multiple projects)
- Set of example strings dynamically extracted from projects

If a project is already cloned, `driver extract-dir` can be used to skip cloning the project.

Many regex databases can be folded into one using `driver db-combine`

### Test Suite Generation -- `driver gen-test-suites`
| Takes as input      | Produces         |
|---------------------|------------------|
| Regex Info Database | Test suites file |

Once we have a corpus of regex info, we can produce a file containing regex test suites. Each
test suite consists of a ground truth regex and a set of example strings that were evaluated on
that regex. The strings are categorized into positive/matching strings and negative/mismatching strings.

### Evaluation -- `driver evaluate`
Actually evaluating...
