mod args;
#[cfg(feature = "extractor")]
mod extraction_results;
#[cfg(feature = "extractor")]
mod setup_extractors;
mod report;
mod commands;
#[cfg(feature = "extractor")]
mod extraction;

use log::{debug, error, LevelFilter, log_enabled};
use std::error::Error;
use std::process::ExitCode;
use clap::Parser;
use subprocess::Exec;
use std::io::Read;
use log::Level::Debug;
use crate::args::{GlobalArgs, Subcommands};
use crate::commands::db_combine::db_combine;
#[cfg(feature = "ecosystem-dump")]
use crate::commands::ecosystem_dump::pull_ecosystem_dump_cmd;
#[cfg(feature = "evaluation")]
use crate::commands::evaluate::evaluate;
#[cfg(feature = "extractor")]
use crate::commands::extract_dir::directory_extract_command;
#[cfg(feature = "extractor")]
use crate::commands::full_extract::full_extract_command;
#[cfg(feature = "evaluation")]
use crate::commands::gen_dfa_db::generate_dfa_db;
#[cfg(feature = "evaluation")]
use crate::commands::gen_test_suites::gen_test_suites_command;
#[cfg(feature = "reporting")]
use crate::commands::report_gen::generate_report;
use crate::commands::sample_unique_projects::sample_unique_projects;

fn main() -> Result<ExitCode, Box<dyn Error>> {
    env_logger::builder()
        .filter_level(LevelFilter::Info)
        .parse_default_env()
        .init();

    let args = GlobalArgs::parse();

    log_path();
    log_npm_version();
    dump_env();

    match args.command {
        #[cfg(feature = "extractor")]
        Subcommands::Extract(extract_args) => {
            full_extract_command(extract_args)
        }
        #[cfg(feature = "extractor")]
        Subcommands::ExtractDir(extract_args) => {
            directory_extract_command(extract_args)
        }
        Subcommands::DbCombine(db_combine_args) => {
            db_combine(db_combine_args)
        }
        #[cfg(feature = "evaluation")]
        Subcommands::GenTestSuites(args) => {
            gen_test_suites_command(args)
        }
        #[cfg(feature = "evaluation")]
        Subcommands::Evaluate(args) => {
            evaluate(args)
        }
        #[cfg(feature = "evaluation")]
        Subcommands::GenDFAs(args) => {
            generate_dfa_db(args)
        }
        #[cfg(feature = "ecosystem-dump")]
        Subcommands::EcosystemDump(args) => {
            pull_ecosystem_dump_cmd(args)
        }
        #[cfg(feature = "reporting")]
        Subcommands::ReportGen(args) => {
            generate_report(args)
        }
        Subcommands::SamplePackages(args) => {
            sample_unique_projects(args)
        }
    }
}

fn log_path() {
    if log_enabled!(Debug) {
        match std::env::var("PATH") {
            Ok(path_val) => {
                debug!("PATH={}", path_val)
            }
            Err(err) => {
                error!("error while retrieving path: {}", err)
            }
        }
    }
}

fn log_npm_version() {
    if log_enabled!(Debug) {
        let mut version_text = String::default();
        Exec::cmd("npm")
            .arg("--version")
            .stream_stdout()
            .unwrap()
            .read_to_string(&mut version_text).unwrap();

        debug!("npm version:\n{}", version_text);
    }
}

fn dump_env() {
    if log_enabled!(Debug) {
        debug!("env dump begin:");
        for (key, value) in std::env::vars() {
            eprintln!("{}={}", key, value);
        }
        debug!("env dump end")
    }
}
