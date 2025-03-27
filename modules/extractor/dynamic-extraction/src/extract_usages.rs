use std::collections::HashMap;
use log::{error, info, trace, warn};
use shared::package_spec::PackageSpec;
use shared::processing_result::ProcessingResult;
use shared::usage::{RawUsageRecord, UsageRecord};
use std::error::Error;
use std::fs::File;
use std::io::{BufRead, BufReader};
use std::path::{Path, PathBuf};
use crate::dynamic_extractor_manager::DynamicExtractorManager;

/// Extract all dynamic usages from a project. This function performs the following steps:
/// 1. Perform any preprocessing on linters
/// 2. run npm install
/// 3. run npm test
/// 4. collect log results
/// 
/// Returns a processing result for the given package
pub fn extract_dynamic_usages(
    package_spec: &PackageSpec,
    project_path: &Path,
    dynamic_extractor: &dyn DynamicExtractorManager
) -> Result<ProcessingResult<Vec<UsageRecord>>, Box<dyn Error>>
{
    // start by preprocessing
    let pre_install_status = dynamic_extractor.pre_install(package_spec, project_path)?;
    match pre_install_status {
        ProcessingResult::UnsupportedBuildTool => {
            return Ok(ProcessingResult::UnsupportedBuildTool)
        }
        ProcessingResult::Okay(_) => {
            info!("pre-installation checks passed for {}", package_spec.name());
        }
        status => unreachable!("Processing result {:?} is not supported from pre_install", status)
    }
    
    // run npm install
    info!(
        "Installing dependencies and building package {}...",
        package_spec.name()
    );
    let install_status = dynamic_extractor.install_deps(package_spec, project_path)?;
    match install_status {
        ProcessingResult::InstallFailed(err) => return Ok(ProcessingResult::InstallFailed(err)),
        ProcessingResult::InstallTimeout => return Ok(ProcessingResult::InstallTimeout),
        ProcessingResult::Okay(_) => {
            info!(
                "Successfully installed dependencies for package {}",
                package_spec.name(),
            );
        }
        _ => unreachable!(),
    }

    dynamic_extractor.build_pkg(package_spec, project_path)?;

    // run npm test
    let intermediate_results_path = create_intermediate_file_name(package_spec);
    info!(
        "Starting to run test suite and collect examples for package {}...",
        package_spec.name()
    );
    let test_suite_execution_result = dynamic_extractor.run_test_suite(package_spec, project_path, &intermediate_results_path)?;
    
    let collect_results = collect_examples(
        project_path,
        &intermediate_results_path,
        test_suite_execution_result,
        dynamic_extractor.example_limit()
    )?;

    if intermediate_results_path.exists() {
        match std::fs::remove_file(&intermediate_results_path) {
            Ok(_) => trace!(
                "Successfully deleted intermediate results file '{}'",
                intermediate_results_path.to_string_lossy()
            ),
            Err(err) => error!(
                "Failed to remove intermediate results file '{}': {}",
                intermediate_results_path.to_string_lossy(),
                err
            ),
        }
    }

    match collect_results {
        ProcessingResult::Partial { results, error } => {
            let inflated_entities = inflate_raw_usages(results, package_spec, project_path);
            Ok(ProcessingResult::Partial {
                results: inflated_entities,
                error: error.change_type::<Vec<UsageRecord>>().into(),
            })
        }
        ProcessingResult::Okay(usages) => {
            let inflated_entities = inflate_raw_usages(usages, package_spec, project_path);
            Ok(ProcessingResult::Okay(inflated_entities))
        }
        other_result => Ok(other_result.change_type()),
    }
}

/// run the test suite and collect examples. This call `npm test` and parses all raw usages from
/// the intermediate file.
fn collect_examples(
    base_path: &Path,
    collect_examples_path: &Path,
    test_suite_result: ProcessingResult<()>,
    example_limit: Option<u32>,
) -> Result<ProcessingResult<Vec<RawUsageRecord>>, Box<dyn Error>> {
    // if there is not a test suite, we don't have to do anything
    if let ProcessingResult::NoTestSuite = &test_suite_result {
        info!("project {} had no test suite, so skipping", base_path.to_string_lossy());
        return Ok(ProcessingResult::NoTestSuite)
    }
    
    // actually read raw usages
    let raw_usages = read_raw_usages(collect_examples_path);
    let original_length = raw_usages.len();
    let pruned_usages = discard_extra_examples(raw_usages, example_limit);
    if pruned_usages.len() < original_length {
        let diff = original_length - pruned_usages.len();
        warn!("While dynamically extracting project {}: discarded {} examples due to limit being {}", base_path.to_string_lossy(), diff, example_limit.unwrap_or_default());
    }
    
    // if the test suite didn't have an error, then there's nothing special we have to do -- just
    // report an okay
    if let ProcessingResult::Okay(_) = &test_suite_result {
        return Ok(ProcessingResult::Okay(pruned_usages));
    }
    
    // otherwise, we need to figure out what our partial result is going to be
    Ok(ProcessingResult::Partial {
        results: pruned_usages,
        error: Box::new(test_suite_result.change_type()),
    })
}

fn read_raw_usages(path: &Path) -> Vec<RawUsageRecord> {
    let Ok(collect_file) = File::open(path) else {
        return vec![];
    };

    let mut results: Vec<RawUsageRecord> = Vec::new();
    let reader = BufReader::new(collect_file);
    for line in reader.lines() {
        let Ok(line) = line else {
            continue;
        };
        // skip any that you can't parse
        let record_result = serde_json::from_str::<RawUsageRecord>(&line);
        let Ok(raw_usage) = record_result else {
            warn!("failed to parse usage '{}'", line);
            warn!("json parse error: {}", record_result.unwrap_err());
            continue;
        };
        results.push(raw_usage);
    }

    results
}

fn inflate_raw_usages(
    usages: Vec<RawUsageRecord>,
    package_spec: &PackageSpec,
    base_path: &Path,
) -> Vec<UsageRecord> {
    usages
        .into_iter()
        .map(|raw_usage| UsageRecord::from_parsed(raw_usage, package_spec, base_path))
        .collect()
}

fn discard_extra_examples(records: Vec<RawUsageRecord>, limit: Option<u32>) -> Vec<RawUsageRecord> {
    
    if limit.is_none() || records.is_empty() {
        return records;
    }
    
    let limit = limit.unwrap() as usize;
    
    let mut pattern_examples: HashMap<String, Vec<RawUsageRecord>> = HashMap::new();
    
    for record in records {
        
        if let Some(saved_records) = pattern_examples.get_mut(record.pattern()) {
            if saved_records.len() > limit {
                continue;
            }
            
            saved_records.push(record);
        } else {
            pattern_examples.insert(record.pattern().to_string(), vec![record]);
        }
    }
    
    pattern_examples.into_values()
        .flat_map(|vec| vec.into_iter())
        .collect()
}

fn create_intermediate_file_name(spec: &PackageSpec) -> PathBuf {
    let sanitized_name = spec.name()
        .replace("/", "-")
        .replace("@", "");
    
    std::env::temp_dir().join(format!("{}-results.ndjson", sanitized_name))
}
