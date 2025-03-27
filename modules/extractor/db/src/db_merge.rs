use std::path::Path;
use rusqlite::{Connection, Error, named_params};

pub enum MergeDatabaseVersion {
    V1,
    V2,
}

/// merges the [to_merge_path] database into the [accumulator_db_path] database
pub fn merge_databases(accumulator_db_path: &Path, to_merge_path: &Path, version: &MergeDatabaseVersion) -> Result<(), Error> {
    // open both databases
    let accumulator = Connection::open(accumulator_db_path)?;
    // NOTE: it is VERY important that it is named merge_db
    accumulator.execute(
        "ATTACH DATABASE :db_name AS merge_db",
        named_params! {
            ":db_name": to_merge_path.to_string_lossy()
        }
    )?;
    
    execute_query(&accumulator, version)
}

fn execute_query(connection: &Connection, version: &MergeDatabaseVersion) -> Result<(), Error> {
    let query = match version {
        MergeDatabaseVersion::V1 => include_str!("sql/merge_dbs.sql"),
        MergeDatabaseVersion::V2 => include_str!("sql/merge_dbs_v2.sql"),
    };
    connection.execute_batch(query)
}
