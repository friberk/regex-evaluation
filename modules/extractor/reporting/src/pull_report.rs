use std::error::Error;
use std::path::Path;
use log::info;
use rusqlite::{Connection, OpenFlags};
use db::is_metachar_regex::load_is_metachar_regex_function;
use crate::report::CharacteristicsReport;
use crate::report_def::ReportDefinition;

/// Use definitions to prepare all reports
pub fn pull_reports(db_path: &Path, defs: Vec<ReportDefinition>) -> Result<CharacteristicsReport, Box<dyn Error>> {
    let db_connection = Connection::open_with_flags(db_path, OpenFlags::SQLITE_OPEN_READ_ONLY)?;

    // provide special function
    load_is_metachar_regex_function(&db_connection)?;

    let mut report = CharacteristicsReport::new();
    for report_def in defs.into_iter().filter(|def| !def.ignored()) {
        info!("starting to pull {}", report_def.name.as_str());
        let report_data = report_def.pull_report(&db_connection)?;
        report.push_report(report_data, report_def);
    }
    
    Ok(report)
}
