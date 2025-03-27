use std::collections::HashMap;
use std::error::Error;
use std::fs::File;
use std::process::ExitCode;
use log::{error, info};
use db::db_client::RegexDBClient;
use shared::cloc::{ClocHarness};
use shared::package_spec::{PackageSpec, read_many_from_file};
use crate::args::{CommonExtractArgs, ExtractArgs, ProcessMode, ProvidesCommonExtractArgs};
use crate::extraction::process_packages::PackageProcessorRef;
use crate::extraction::save_execution_results::save_execution_results;
use crate::report::ProcessingReport;
use crate::setup_extractors::{build_dynamic_extractor_map, ExtractorMapBuilder};

pub fn full_extract_command(args: ExtractArgs) -> Result<ExitCode, Box<dyn Error>> {
    if args.package_spec_paths().is_empty() {
        info!("No input files provided. No work to be done");
        return Ok(ExitCode::SUCCESS);
    }

    /*
     * 0. project setup:
     *   - initialize extractors
     *   - connect to database
     */
    info!("Setting up extractor map");
    let extractor_map = match ExtractorMapBuilder::new(args.common_args()).with_all().setup_extractor_map() {
        Ok(map) => map,
        Err(err) => {
            error!("Error while setting up extractor map: {}", err);
            return Err(err);
        }
    };
    info!("Extractor map successfully initialized");

    let dynamic_extractor_map = build_dynamic_extractor_map(args.common_args());
    info!("successfully initialized dynamic extractor map");

    info!("Setting up cloc harness...");
    let cloc_tool = match ClocHarness::new_from_env() {
        Ok(harness) => {
            info!("successfully initialized cloc tool");
            harness
        }
        Err(err) => {
            error!("Error while setting up cloc harness: {}", err);
            return Err(err.into());
        }
    };

    let package_processor = PackageProcessorRef::new(&extractor_map, &dynamic_extractor_map, &cloc_tool);

    // 1. read in project specifications
    let mut all_package_specs = Vec::<PackageSpec>::new();
    for spec_file in args.package_spec_paths() {
        let specs = match read_many_from_file(spec_file) {
            Ok(items) => {
                info!("read {} packages specs from input file {}", items.len(), spec_file.to_string_lossy());
                items
            }
            Err(err) => {
                error!("error while opening input file '{}': {}", spec_file.to_string_lossy(), err);
                return Err(err)
            }
        };
        all_package_specs.extend(specs);
    }
    // filter down to unique repositories
    let associated_packages = unique_repository_specs(all_package_specs);
    
    // 2. actually do processing. The behavior here changes depending on what is configured
    
    info!("execution processing pipeline in {} mode", args.process_mode());
    let report = match args.process_mode() {
        ProcessMode::Incremental => incremental_processing(associated_packages, package_processor, &args),
        ProcessMode::Batch => batch_processing(associated_packages, package_processor, &args)
    }?;

    // save the report
    if let Some(report_path) = args.common_args().report() {
        let report_file = File::create(report_path)?;
        serde_json::to_writer(report_file, &report)?;
        info!("wrote report to {}", report_path.to_string_lossy());
    }
    
    info!("successfully executed extraction");
    
    Ok(ExitCode::SUCCESS)
}

fn batch_processing<'parent>(
    associated_packages: HashMap<PackageSpec, Vec<PackageSpec>>,
    package_processor: PackageProcessorRef<'parent>,
    args: &ExtractArgs,
) -> Result<ProcessingReport, Box<dyn Error + 'static>> {

    let results = package_processor.process_packages(associated_packages.keys(), &args)?;
    let execution_results = results.into_iter()
        .map(|(spec, result)| (spec.clone(), result))
        .collect::<HashMap<_, _>>();
    // these should be the same length
    assert_eq!(execution_results.len(), associated_packages.len());

    // 2.5. clean up the maven install directory if requested
    if args.common_args().mvn_install_dir().is_some() && args.common_args().mvn_install_cleanup() {
        let install_dir = args.common_args().mvn_install_dir().as_ref().unwrap();
        match std::fs::remove_dir_all(install_dir) {
            Ok(_) => {
                info!("successfully deleted intermediate mvn install directory {}", install_dir.to_string_lossy());
            }
            Err(err) => {
                error!("error while deleting mvn install path '{}': {}", install_dir.to_string_lossy(), err)
            }
        }
    }

    // 3. combine results
    info!("Connecting to database...");
    let mut db_client = configure_database(args.common_args())?;
    info!("connected!");
    let report = save_execution_results(associated_packages, execution_results, &mut db_client)?;

    Ok(report)
}

fn incremental_processing<'parent, PackagesT>(
    specs: PackagesT,
    package_processor: PackageProcessorRef<'parent>,
    args: &ExtractArgs,
) -> Result<ProcessingReport, Box<dyn Error + 'static>>
where PackagesT: IntoIterator<Item=(PackageSpec, Vec<PackageSpec>)>
{
    // 1. setup database and processing report ahead of time
    info!("Connecting to database...");
    let mut db_client = configure_database(args.common_args())?;
    info!("connected!");

    let mut processing_report = ProcessingReport::default();

    // process packages and save as we go
    package_processor.process_packages_incremental(specs, args, &mut db_client, &mut processing_report)?;

    Ok(processing_report)
}

fn configure_database(args: &CommonExtractArgs) -> Result<RegexDBClient, Box<dyn Error>> {
    let db = match RegexDBClient::new(args.output()) {
        Ok(client) => { client }
        Err(err) => {
            error!("Error while setting up regex db: {}", err);
            return Err(err.into());
        }
    };

    match db.initialize_regex_database() {
        Ok(_) => {
            info!("Successfully initialized regex database at {}", args.output().display());
        }
        Err(err) => {
            error!("Error while initializing database: {}", err);
            return Err(err.into())
        }
    };

    db.set_synchronous_pragma(args.synchronous_db().to_db_param())?;
    Ok(db)
}

/// associate all project specs by repo so that we only clone/process each repository once
fn unique_repository_specs(packages_specs: Vec<PackageSpec>) -> HashMap<PackageSpec, Vec<PackageSpec>> {
    let mut unique_by_repo = HashMap::<String, Vec<PackageSpec>>::new();
    for spec in packages_specs {
        if let Some(existing) = unique_by_repo.get_mut(spec.repo()) {
            existing.push(spec);
        } else {
            unique_by_repo.insert(String::from(spec.repo()), vec![spec]);
        }
    }
    
    // for each one of these, the first is the parent and the rest are dependent
    let mut parent_and_dependents = HashMap::<PackageSpec, Vec<PackageSpec>>::new();
    for mut specs in unique_by_repo.into_values() {
        assert!(!specs.is_empty());
        let first = specs.remove(0);
        parent_and_dependents.insert(first, specs);
    }
    
    parent_and_dependents
}
