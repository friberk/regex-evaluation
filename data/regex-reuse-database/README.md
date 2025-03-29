# regex-reuse-database

Due to the large size of the database, we share it on Zenodo. You can view and download the database from this link: https://zenodo.org/records/15098946?preview=1&token=eyJhbGciOiJIUzUxMiJ9.eyJpZCI6ImM3MTkyNDJhLTY4ZjQtNGE1NS04OGFkLTE5MTkxZGZhNTQ2YSIsImRhdGEiOnt9LCJyYW5kb20iOiJkODBiZWYxYzhmM2JkZDBlZGIyNjY5YzNlOTUyMTZjZiJ9.YLbBea1s5pRNtbSH43IchvaLQapf6DaDdWEzqo_jAB9MY3nVjCcu2Hea-6B6QQUYkA_VmBoNZ7PceIZfO-oEJg

## Database Files

- `oss-regexes.sqlite.tar.xz` contains the SQLite DB for regexes and their corresponding test suites (if they exist) collected from open-source software projects.
- `internet-regexes.sqlite.tar.xz` contains the SQLite DB for regexes and their corresponding test suites (only for RegExLib regexes) collected from RegExLib and Stack Overflow. Note that Stack Overflow regexes have not been used and evaluated in this version of the paper, and we are presenting them to the research community as extra data.

## Database Structure

One of the most important files in use for data collection is the regex database. This file is a SQLite database that contains
pretty much all raw data used in this project. We typically interact with this database using the `sqlite3` client, which is
the default client. You can use anything else, but that's the one that we typically use.

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
