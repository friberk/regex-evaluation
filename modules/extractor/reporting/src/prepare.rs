use rusqlite::Connection;

/// Creates all temporary tables that reports are pulled from
pub fn prepare_views(db_connection: &Connection) -> rusqlite::Result<()> {
    let characteristics_table_query = include_str!("sql/characteristics_tables.sql");
    db_connection.execute_batch(characteristics_table_query)
}
