
# DB

The DB Module provides common database operations. Its main contribution is providing a Regex DB Client, which wraps common SQL queries and operations.
Use this to interact with the database when possible. All queries for all projects are included here, which is not an amazing choice. That being said,
all DB interaction should belong here.

To learn about the extractor database schema, visit the [create_tables.sql](src/sql/create_tables.sql) file. These tables are created by this project.
Note: there are more tables than these, but they are created by different projects, so consult that documentation for info about those tables.

## General Design
- The `sql` directory contains raw SQL queries. These queries are included into the binary using `include!` macros. This ensures that queries are available
  in the binary without additional resource location.
- This project uses [rusqlite](https://docs.rs/rusqlite/latest/rusqlite/) for SQLite interaction. Please consult its documentation for more information.
- The `RegexDBClient` owns the connection to the database. This object holds the connection and provides methods for setting up the database and more. It
  can also be dereferenced as a SQLite connection, so you can essentially use it as a `rusqlite::Connection` object.
- `RegexDBOperator` is the object actually resposible for performing operations on the database. This design decision was mode to allow you to have transaction
  flexibility. Essentially, it takes in a connection and performs sql queries on that connection. If you want to perform one-off operations, just wrap
  your client. If you want to perform operations in a transaction, create an operator that holds a transaction instead.
- `regex_filter` provides some nice extension functions that are available to your SQL queries. These functions perform filtering and other things.

There's other stuff that isn't really used any more. e.g., `dfa_db`.
