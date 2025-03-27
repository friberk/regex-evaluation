use std::error::Error;
use std::fs::File;
use std::process::ExitCode;
use log::{error, info};
use db::db_client::RegexDBClient;
use evaluation::query_test_suites::{query_test_suite_matches};
use shared::test_case::RegexTestCase;
use crate::args::EvaluationArgs;

/// Performs reuse evaluation on a single database.
pub fn evaluate(args: EvaluationArgs) -> Result<ExitCode, Box<dyn Error>> {

    // connect to database
    info!("opening connection to database {}", args.database_file.to_string_lossy());
    let mut db_client = RegexDBClient::new(&args.database_file)?;

    let test_suites = if let Some(test_cases_path) = &args.test_cases_path {
        info!("loading test cases from {}", test_cases_path.to_string_lossy());
        let test_cases_file = File::open(test_cases_path)?;
        let test_suites: Vec<RegexTestCase> = serde_json::from_reader(test_cases_file)?;
        info!("loaded {} test suites", test_suites.len());
        test_suites
    } else {
        info!("pulling test suites from database now");
        let test_suites = db_client.pull_test_suites()?;
        info!("loaded {} test suites", test_suites.len());
        test_suites
    };

    info!("starting test suite matches...");
    let test_suite_matches = match query_test_suite_matches(&mut db_client, &args.dfas_db, &test_suites) {
        Ok(matches) => matches,
        Err(err) => {
            error!("error while querying test suite matches: {}", err);
            return Ok(ExitCode::FAILURE);
        }
    };
    
    let output = File::create(&args.output)?;
    
    serde_json::to_writer_pretty(output, &test_suite_matches)?;

    info!("wrote {} results to {}", test_suite_matches.len(), args.output.to_string_lossy());
    
    Ok(ExitCode::SUCCESS)
}
