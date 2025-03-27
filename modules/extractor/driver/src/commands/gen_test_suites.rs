use std::error::Error;
use std::fs::File;
use std::process::ExitCode;
use log::{error, info};
use db::db_client::RegexDBClient;
use crate::args::GenTestSuitesArgs;

pub fn gen_test_suites_command(args: GenTestSuitesArgs) -> Result<ExitCode, Box<dyn Error>> {

    info!("connecting to database");
    let mut connection = match RegexDBClient::new(&args.database_file) {
        Ok(conn) => conn,
        Err(err) => {
            error!("error while connecting to database: {}", err);
            return Ok(ExitCode::FAILURE)
        }
    };
    info!("connected to database");

    info!("pulling tests suites...");
    let test_suites = match connection.pull_test_suites() {
        Ok(tests) => tests,
        Err(err) => {
            error!("error while pulling test suites: {}", err);
            return Ok(ExitCode::FAILURE)
        }
    };
    info!("pulled {} test suites", test_suites.len());

    let output_file = match File::create(&args.output) {
        Ok(f) => f,
        Err(err) => {
            error!("error while opening output file: {}", err);
            return Ok(ExitCode::FAILURE)
        }
    };

    if let Err(err) = serde_json::to_writer_pretty(output_file, &test_suites) {
        error!("error while connecting to database: {}", err);
        return Ok(ExitCode::FAILURE)
    }

    info!("successfully outputted results to {}", args.output.to_string_lossy());

    Ok(ExitCode::SUCCESS)
}