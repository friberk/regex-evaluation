use std::collections::HashMap;
use std::error::Error;
use std::fs::File;
use std::process::ExitCode;
use log::info;
use db::db_client::RegexDBClient;
use shared::cloc::ClocHarness;
use crate::args::{DirExtractArgs, ProvidesCommonExtractArgs};
use crate::extraction::process_packages::PackageProcessorRef;
use crate::extraction::save_execution_results::save_execution_results;
use crate::setup_extractors::{build_dynamic_extractor_map, ExtractorMapBuilder};

pub fn directory_extract_command(args: DirExtractArgs) -> Result<ExitCode, Box<dyn Error>> {
    let package_spec = args.package_spec().expect("filename should be present");

    let extractors = ExtractorMapBuilder::new(args.common_args())
        .with_lang(package_spec.language().clone())
        .setup_extractor_map()?;
    
    let dynamic_extractors = build_dynamic_extractor_map(args.common_args());

    let cloc_tool = ClocHarness::new_from_env()?;
    
    let package_processor = PackageProcessorRef::new(&extractors, &dynamic_extractors, &cloc_tool);
    
    let abs_pkg_dir = args.directory().canonicalize()?;
    let result = package_processor.process_package_dir(&package_spec, &abs_pkg_dir, &args)?;
    info!("package {} finished with result: {}", package_spec.name(), result);

    let associated_packages = HashMap::from([(package_spec.clone(), Vec::default())]);
    let results_map = HashMap::from([(package_spec, result)]);

    let mut db_client = RegexDBClient::new(args.common_args().output())?;
    db_client.initialize_regex_database()?;
    let report = save_execution_results(associated_packages, results_map, &mut db_client)?;

    info!("successfully saved results");
    
    // write the report if specified
    if let Some(report_path) = args.common_args().report() {
        let report_file = File::create(report_path)?;
        serde_json::to_writer(report_file, &report)?;
    }

    Ok(ExitCode::SUCCESS)
}
