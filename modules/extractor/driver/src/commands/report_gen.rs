use std::error::Error;
use std::fs::File;
use std::io::Read;
use std::ops::Not;
use std::path::PathBuf;
use std::process::ExitCode;
use log::{error, info};
use serde::{Deserialize, Serialize};
use reporting::pull_report::pull_reports;
use reporting::report_def::ReportDefinition;
use crate::args::{ReportFilter, ReportFilterMode, ReportFormat, ReportGenArgs};

pub fn generate_report(args: ReportGenArgs) -> Result<ExitCode, Box<dyn Error>> {

    let report_defs = match read_report_defs(args.def) {
        Ok(defs) => {
            info!("successfully read reports definitions");
            defs
        }
        Err(err) => {
            error!("error while reading report defs: {}", err);
            return Ok(ExitCode::FAILURE)
        }
    };

    let gen_report_filter = create_report_filter(args.filter);
    let report_defs = report_defs.into_iter()
        .filter(gen_report_filter)
        .collect::<Vec<_>>();

    info!("pulling report from {}...", args.db_file.to_string_lossy());
    let report = pull_reports(args.db_file.as_path(), report_defs)?;
    info!("successfully pulled report");

    match args.format {
        ReportFormat::Xlsx => {
            info!("writing report in xlsx format to {}...", args.output.to_string_lossy());
            report.write_to_xlsx(args.output.as_path())?;
        }
        #[cfg(json_report)]
        ReportFormat::Json => {
            let report_file = File::create(args.output.as_path())?;
            serde_json::to_writer(report_file, &report)?;
        }
        ReportFormat::Csv => {
            info!("writing report in CSV format to base directory {}...", args.output.display());
            report.write_to_csv(args.output.as_path())?;
        }
        _ => panic!("unsupported report format")
    }

    info!("successfully generated report");

    Ok(ExitCode::SUCCESS)
}

#[derive(Debug, Serialize, Deserialize)]
struct ReportFile {
    report: Vec<ReportDefinition>
}

fn read_report_defs(def_path: PathBuf) -> Result<Vec<ReportDefinition>, Box<dyn Error>> {
    let mut def_file = File::open(def_path)?;
    let mut contents = String::default();
    def_file.read_to_string(&mut contents)?;
    let defs = toml::from_str::<ReportFile>(&contents)?;
    Ok(defs.report)
}

/// creates a filter that'll filter out excluded/included reports
fn create_report_filter(report_filter: ReportFilter) -> impl Fn(&ReportDefinition) -> bool {
    let filter_mode = ReportFilterMode::from(report_filter);
    move |report_definition: &ReportDefinition| {
        match &filter_mode {
            ReportFilterMode::None => true,
            ReportFilterMode::Include(included_ids) => included_ids.contains(report_definition.id()),
            ReportFilterMode::Exclude(excluded_ids) => excluded_ids.contains(report_definition.id()).not(),
        }
    }
}
