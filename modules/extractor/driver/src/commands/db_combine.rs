use std::error::Error;
use std::process::ExitCode;
use log::{error, info, warn};
use promptly::prompt_default;
use db::db_client::RegexDBClient;
use db::db_merge::merge_databases;
use crate::args::DbCombineArgs;

/// This command is responsible for combining different databases. Each extraction process is going
/// to produce its own SQLite database. This command is a tool for the experimenter to combine two
/// databases into one. We can either write the combined results into a new database, or both
/// databases can be folded into one.
pub fn db_combine(args: DbCombineArgs) -> Result<ExitCode, Box<dyn Error>> {

    if args.database_files.is_empty() {
        info!("no files provided, nothing to do");
        return Ok(ExitCode::SUCCESS);
    }
    
    // we need at least two files
    if args.database_files.len() <= 1 && args.existing.is_none() && args.new.is_none() {
        println!("At least two files must be provided. Done");
        return Ok(ExitCode::SUCCESS)
    }

    // if we are purging, find out if we should keep going
    if args.purge {
        if !args.confirm {
            println!("You have specified purge mode, which will delete the databases that you merge.");
            let result = prompt_default("Are you sure you want to continue: ", false)?;
            if !result {
                println!("Did not confirm, exiting...");
                return Ok(ExitCode::FAILURE);
            }
        } else {
            warn!("entering purge mode as confirmed by command line flag");
        }
    }

    let accumulator_db = if let Some(new_path) = &args.new {
        let new_db_conn = RegexDBClient::new(new_path)?;
        new_db_conn.initialize_regex_database()?;
        new_path
    } else if let Some(existing_path) = &args.existing {
        existing_path
    } else {
        args.database_files.first().unwrap()
    };
    
    let skip_offset = if args.new.is_some() || args.existing.is_some() {
        0usize
    } else {
        1usize
    };
    
    let db_merge_version = args.version();
    
    for remainder in args.database_files().iter().skip(skip_offset) {
        
        if remainder == accumulator_db {
            warn!("Skipping {} because it is the same path as the accumulator", remainder.to_string_lossy());
            continue;
        }
        
        match merge_databases(accumulator_db, remainder, &db_merge_version) {
            Ok(_) => {
                info!("successfully merged {} into {}", remainder.display(), accumulator_db.display());
                if args.purge {
                    match std::fs::remove_file(remainder) {
                        Ok(_) => {
                            info!("successfully deleted {}", remainder.display());
                        }
                        Err(err) => {
                            error!("error while deleting {}: {}", remainder.display(), err);
                        }
                    }
                }
            }
            Err(err) => {
                error!("error while merging {} into {}: {}", remainder.to_string_lossy(), accumulator_db.to_string_lossy(), err);
            }
        }
    }

    info!("successfully merged databases");

    Ok(ExitCode::SUCCESS)
}
