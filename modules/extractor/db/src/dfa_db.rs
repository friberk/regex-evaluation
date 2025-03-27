use std::error::Error;
use std::io::Write;
use std::path::Path;
use log::{debug, warn};
use rusqlite::blob::ZeroBlob;
use rusqlite::{Connection, DatabaseName, named_params};

pub fn create_dfa_database(corpus_path: &Path, dfa_path: &Path) -> Result<(), Box<dyn Error>> {
    let mut connection = Connection::open(dfa_path)?;
    compile_regexes(corpus_path, &mut connection)
}

fn compile_regexes(corpus_database_path: &Path, connection: &mut Connection) -> Result<(), Box<dyn Error>> {

    // attach the main regex corpus database
    const CORPUS_DB_SCHEMA: &str = "corpus";
    connection.execute(
        "ATTACH DATABASE :database_path AS :database_schema",
        named_params! {
            ":database_path": corpus_database_path.to_string_lossy(),
            ":database_schema": CORPUS_DB_SCHEMA
        }
    )?;

    // create the table we need in this database
    create_dfa_table(&connection)?;

    // query all regexes from the corpus database, compile regex patterns into DFAs, and store them
    // into the database

    let mut select_regexes_stmt = connection.prepare("\
        SELECT id, pattern FROM corpus.regex_entity
    ")?;

    let row_tuple_iter = select_regexes_stmt.query_map(
        named_params! {
        },
        |row| {
            let id: usize = row.get(0)?;
            let pattern: String = row.get(1)?;

            Ok((id, pattern))
        }
    )?.filter_map(|row_tuple| row_tuple.ok());

    for (id, pattern) in row_tuple_iter {
        // this is a deliberate choice to use spare to try to reduce size
        debug!("starting to compile regex {} /{}/", id, pattern);
        let Ok(regex) = regex_automata::dfa::sparse::DFA::new(&pattern) else {
            warn!("failed to compile regex {} /{}/", id,  pattern);
            continue;
        };
        debug!("successfully compiled DFA for regex {} /{}/", id, pattern);

        let mut insert_stmt = connection.prepare_cached("INSERT INTO dfa_blobs (regex_id, dfa) VALUES (:regex_id, :dfa)")?;

        let regex_bytes = regex.to_bytes_native_endian();
        insert_stmt.execute(named_params! {
            ":regex_id": id,
            ":dfa": ZeroBlob(regex_bytes.len() as i32)
        })?;

        let last_row_id = connection.last_insert_rowid();

        let Ok(mut blob_handle) = connection.blob_open(DatabaseName::Main, "dfa_blobs", "dfa", last_row_id, false) else {
            warn!("failed to open blob for {}", last_row_id);
            continue;
        };

        blob_handle.write_all(&regex_bytes)?;

        debug!("successfully stored DFA for regex {} /{}/", id, pattern);
    }

    Ok(())
}

fn create_dfa_table(connection: &Connection) -> Result<(), rusqlite::Error> {
    let query = include_str!("sql/dfa_table.sql");
    connection.execute(query, [])
        .map(|_| ())
}

#[cfg(test)]
mod tests {

    #[test]
    fn can_compile_regex() {
        const REGEX: &str = r"^\\,|\\,$|^~|~$|^\\ |\\ $|^\\thinspace|\\thinspace$|^\\!|\\!$|^\\:|\\:$|^\\;|\\;$|^\\enspace|\\enspace$|^\\quad|\\quad$|^\\qquad|\\qquad$|^\\hspace{[a-zA-Z0-9]+}|\\hspace{[a-zA-Z0-9]+}$|^\\hfill|\\hfill$";
        regex_automata::meta::Regex::new(REGEX).expect_err("should fail to compile for DFA");
        regex::Regex::new(REGEX).expect_err("should fail to compile on normal regex");
    }
}
