use std::collections::HashSet;
use std::error::Error;
use std::io::Read;
use std::path::Path;
use regex_automata::dfa::sparse::DFA;
use rusqlite::{Connection, DatabaseName, named_params};
use serde::Serialize;
use db::db_client::RegexDBClient;
use log::{debug, warn};
use shared::test_case::RegexTestCase;

#[derive(Serialize, Hash, Eq, PartialEq)]
pub struct RegexResult {
    regex_id: usize,
    pattern: String,
}

#[derive(Serialize)]
pub struct TestResults<'test_case> {
    /// a given test case
    test_case: &'test_case RegexTestCase,
    /// set of regex entity ids that satisfy the given test case
    matches: HashSet<RegexResult>
}

const DFA_DB_SCHEMA_NAME: &str = "dfas";

pub fn query_test_suite_matches<'a>(db_client: &mut RegexDBClient, dfa_db_path: &Path, test_cases: &'a [RegexTestCase]) -> Result<Vec<TestResults<'a>>, Box<dyn Error>> {

    // attach the DFA corpus database
    db_client.execute(
        "ATTACH DATABASE :db_path AS :db_name",
        named_params! {
            ":db_path": dfa_db_path.to_string_lossy(),
            ":db_name": DFA_DB_SCHEMA_NAME
        }
    )?;

    let query = include_str!("sql/select_evaluation_regexes.sql");
    let mut query = db_client.prepare_cached(query)?;

    let mut results = Vec::<TestResults<'a>>::new();
    for test_case in test_cases {

        let candidate_regex_ids = query.query_map(
            &[(":project_id", &test_case.package_id())],
            |row| {
                let regex_id: usize = row.get(0)?;
                Ok(regex_id)
            }
        )?.filter_map(|item| item.ok())
            .collect::<HashSet<_>>();

        debug!("found candidates {:?} for regex {}", candidate_regex_ids, test_case.truth());

        let mut matching_regexes = HashSet::new();

        for candidate in candidate_regex_ids {
            let regex_dfa = load_dfa_for_regex(&db_client, candidate)?;
            let Some(regex_dfa) = regex_dfa else {
                // warn!("regex {} failed to compile or wasn't found in DFA database, so it cannot be considered", candidate);
                continue
            };

            match test_case.test_regex_dfa(&regex_dfa) {
                Ok(matches) => if matches {
                    matching_regexes.insert(candidate);
                }
                Err(match_err) => {
                    warn!("regex {} failed while performing search on test suite: {}", candidate, match_err);
                }
            }
        }

        let matches = inflate_match_ids(&db_client, matching_regexes)?;
        
        results.push(TestResults {
            test_case,
            matches
        });
    }

    Ok(results)
}

fn inflate_match_ids(connection: &Connection, candidates: HashSet<usize>) -> rusqlite::Result<HashSet<RegexResult>> {
    let mut stmt = connection.prepare("SELECT id, pattern FROM regex_entity WHERE id = :id")?;
    let mut results = HashSet::<RegexResult>::new();
    for candidate in candidates {
        let row_result = stmt.query_row(
            named_params! {":id": candidate},
            |row| {
                let regex_id: usize = row.get(0)?;
                let pattern: String = row.get(1)?;
                Ok(RegexResult { regex_id, pattern })
            }
        )?;
        
        results.insert(row_result);
    }
    
    Ok(results)
}

fn load_dfa_for_regex(connection: &Connection, regex_id: usize) -> Result<Option<DFA<Vec<u8>>>, Box<dyn Error>> {
    let row_id = connection.query_row(
        "SELECT rowid FROM dfas.dfa_blobs WHERE dfas.dfa_blobs.regex_id = :regex_id",
        named_params! {
            ":regex_id": regex_id
        },
        |row| {
            let row_id: i64 = row.get(0)?;
            Ok(row_id)
        }
    );

    // check if the regex has something
    let row_id = match row_id {
        Ok(id) => id,
        Err(err) => return match err {
            rusqlite::Error::QueryReturnedNoRows => Ok(None),
            other_err => Err(other_err.into())
        },
    };

    let mut dfa_handle = connection.blob_open(DatabaseName::Attached("dfas"), "dfa_blobs", "dfa", row_id, true)?;
    let mut dfa_blob = Vec::<u8>::new();
    dfa_handle.read_to_end(&mut dfa_blob)?;

    let (dfa, _) = regex_automata::dfa::sparse::DFA::from_bytes(&dfa_blob).expect("Regex DFA should successfully deserialize as sparse DFA");
    Ok(Some(dfa.to_owned()))
}
