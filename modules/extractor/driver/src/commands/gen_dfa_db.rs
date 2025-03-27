use std::error::Error;
use std::process::ExitCode;
use log::{error, info};
use db::dfa_db::create_dfa_database;
use crate::args::GenDFAsArgs;

pub fn generate_dfa_db(args: GenDFAsArgs) -> Result<ExitCode, Box<dyn Error>> {
    info!("starting to create DFA database from {}", &args.corpus_db.to_string_lossy());
    match create_dfa_database(&args.corpus_db, &args.output_db) {
        Ok(_) => {
            info!("successfully created DFA database");
            Ok(ExitCode::SUCCESS)
        }
        Err(err) => {
            error!("failed to create dfa database: {}", err);
            Ok(ExitCode::FAILURE)
        }
    }
}
