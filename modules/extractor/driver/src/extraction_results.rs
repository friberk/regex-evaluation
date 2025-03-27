use std::error::Error;
use std::fmt::{Display, Formatter};
use log::debug;
use serde::Serialize;
use db::db_client::{RegexDBClient, RegexDBOperator};
use shared::cloc::ClocLanguageOutput;
use shared::regex_entity::RegexEntity;
use shared::usage::UsageRecord;

/// Holds the results from performing extraction of a project. It provides a set of regexes and
/// usages from the given project. These extraction results need to be combined late in the process.
#[derive(Debug, Clone, Serialize)]
pub struct ExtractionResults {
    /// the regexes we extracted
    regexes: Vec<RegexEntity>,
    /// the list of regex usages pull from this package
    usages: Vec<UsageRecord>,
    /// loc info for the package
    package_loc: Option<ClocLanguageOutput>,
}

impl ExtractionResults {
    pub fn new(regexes: Vec<RegexEntity>, usages: Vec<UsageRecord>, cloc_info: Option<ClocLanguageOutput>) -> Self {
        Self { regexes, usages, package_loc: cloc_info }
    }
}

impl Display for ExtractionResults {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        writeln!(f, "Got static regexes:")?;
        for entity in &self.regexes {
            // TODO don't use debug here...
            writeln!(f, "\t{:?}", entity)?;
        }
        writeln!(f, "Got dynamic usages:")?;
        for usage in &self.usages {
            // TODO don't use debug here...
            writeln!(f, "\t{:?}", usage)?;
        }
        
        Ok(())
    }
}

/// writes the extraction results to the database. The db client is responsible for the logic of how
/// to actually store everything.
///
/// * `db_client` regex database client to write results to
/// * `parent_project_id` the id of the project that these extraction results came from
/// * `results` actual results to write
pub fn save_extraction_results(db_operator: &RegexDBOperator, parent_project_id: usize, results: &ExtractionResults) -> Result<(), Box<dyn Error>> {
    
    // save loc info
    if let Some(package_loc) = results.package_loc.as_ref() {
        db_operator.insert_project_loc(parent_project_id, package_loc)?;
    } else {
        debug!("cloc language output was null, so skipping for project {}", parent_project_id);
    }
    
    // save all static regexes
    for regex in &results.regexes {
        db_operator.insert_regex_entity(regex, parent_project_id)?;
    }
    
    // save all dynamic usages
    for usage in &results.usages {
        db_operator.insert_regex_subject_usage(usage, parent_project_id)?;
    }
    
    Ok(())
}
