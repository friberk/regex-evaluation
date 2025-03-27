use std::collections::{HashMap, HashSet};
use log::{debug, trace, warn};
use rusqlite::Error;
use shared::test_case::{RegexTestCase};
use crate::db_client::RegexDBClient;

struct RegexTestCaseRow {
    _regex_id: usize,
    pattern: String,
    project_id: usize,
    _source_usage_id: usize,
    subject: String,
    _func: String
}

impl RegexDBClient {

    pub fn pull_test_suites(&mut self) -> Result<Vec<RegexTestCase>, Box<dyn std::error::Error>> {

        let mut associated_examples = HashMap::<(String, usize), Vec<RegexTestCaseRow>>::new();

        for (regex_pattern_and_id, row) in self.pull_test_suites_raw()?.into_iter()
            .map(|row| ((row.pattern.clone(), row.project_id), row)) {

            if let Some(existing_collection) = associated_examples.get_mut(&regex_pattern_and_id) {
                existing_collection.push(row);
            } else {
                associated_examples.insert(regex_pattern_and_id, vec![row]);
            }
        }

        let mut test_cases = Vec::new();

        for ((regex_pattern, project_id), row_set) in associated_examples {
            let mut strings = HashSet::<String>::new();
            for row in &row_set {
                strings.insert(row.subject.clone());
            }

            match RegexTestCase::new(project_id, &regex_pattern, strings) {
                Ok(test_case) => test_cases.push(test_case),
                Err(err) => {
                    warn!("error while creating test suite for /{}/ ({}): {}", regex_pattern, project_id, err);
                }
            }
        }

        Ok(test_cases)
    }

    fn pull_test_suites_raw(&mut self) -> Result<Vec<RegexTestCaseRow>, Error> {
        let (setup_inter_tab, load_test_suites) = Self::load_queries();

        debug!("running setup query");
        trace!("setup query:\n{}", setup_inter_tab);
        self.connection.execute_batch(setup_inter_tab)?;

        debug!("running test suite load query");
        trace!("test suite load query:\n{}", load_test_suites);
        let mut test_suites_stmt = self.connection.prepare(load_test_suites)?;
        let rows = test_suites_stmt.query_map(
            [],
            |row| {
                
                trace!("got row: {:?}", row);
                
                let regex_id: usize = row.get(0)?;
                let pattern: String = row.get(1)?;
                let project_id: usize = row.get(2)?;
                let usage_id: usize = row.get(3)?;
                let example: String = row.get(4)?;
                let func: String = row.get(5)?;

                Ok(RegexTestCaseRow {
                    _regex_id: regex_id,
                    pattern,
                    project_id,
                    _source_usage_id: usage_id,
                    subject: example,
                    _func: func,
                })
            }
        )
            ?.filter_map(|row_entity| row_entity.ok())
            .collect::<Vec<_>>();

        Ok(rows)
    }

    fn load_queries() -> (&'static str, &'static str) {
        let file_contents = include_str!("../sql/pull_test_suites.sql");
        let parts = file_contents.split("--!")
            .take(2)
            .collect::<Vec<_>>();

        (parts[0], parts[1])
    }
}
