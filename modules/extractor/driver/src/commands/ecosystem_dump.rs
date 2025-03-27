use std::error::Error;
use std::fs::File;
use std::io::{BufWriter, Write};
use std::path::Path;
use std::process::ExitCode;
use log::{error, info};
use ecosystems_dump::pull_dump::pull_ecosystem_dump;
use shared::package_spec::PackageSpec;
use crate::args::{EcosystemDumpArgs, OutputFormat};

pub fn pull_ecosystem_dump_cmd(args: EcosystemDumpArgs) -> Result<ExitCode, Box<dyn Error>> {
    let packages = pull_ecosystem_dump(args.db_params(), args.query_params());
    let packages = match packages {
        Ok(packages) => packages,
        Err(err) => {
            error!("Error while pulling dump: {}", err);
            return Err(err);
        }
    };
    info!("Successfully pulled {} packages", packages.len());
    
    match args.format {
        OutputFormat::NDJSON => write_ndjson(packages, &args.output).map(|_| ExitCode::SUCCESS),
        OutputFormat::JSON => write_json(packages, &args.output).map(|_| ExitCode::SUCCESS),
    }?;
    
    info!("successfully wrote results to {}", args.output.to_string_lossy());
    Ok(ExitCode::SUCCESS)
}

fn write_ndjson(packages: Vec<PackageSpec>, path: &Path) -> Result<(), Box<dyn Error>> {
    let mut writer = BufWriter::new(File::create(path)?);
    
    let newline = ['\n' as u8];
    for package in &packages {
        let package_str = serde_json::to_string(package)?;
        writer.write_all(package_str.as_bytes())?;
        writer.write_all(&newline)?;
    }
    
    Ok(())
}

fn write_json(packages: Vec<PackageSpec>, path: &Path) -> Result<(), Box<dyn Error>> {
    let output_file = File::create(path)?;
    serde_json::to_writer(output_file, &packages)?;
    Ok(())
}
