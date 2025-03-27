use std::collections::HashMap;
use std::error::Error;
use std::path::Path;
use log::{error, info, trace};
use db::db_client::RegexDBClient;
use dynamic_extraction::dynamic_extractor_manager::DynamicExtractorMap;
use dynamic_extraction::extract_usages::extract_dynamic_usages;
use shared::clean_up_guard::CleanUpRepoGuard;
use shared::cloc::{ClocError, ClocHarness};
use shared::package_spec::{PackageSpec};
use shared::processing_result::{ProcessingResult};
use shared::repo_utils::clone_or_get_repo;
use static_extraction::extract_package::static_extract_package;
use static_extraction::extractor::ExtractorMap;
use crate::args::{ExtractArgs, ProvidesCommonExtractArgs};
use crate::extraction::save_execution_results::save_package_execution;
use crate::extraction_results::ExtractionResults;
use crate::report::ProcessingReport;

pub struct PackageProcessorRef<'parent>
{
    extractor_map: &'parent ExtractorMap,
    dynamic_extractor_map: &'parent DynamicExtractorMap,
    cloc_tool: &'parent ClocHarness,
}

impl<'parent> PackageProcessorRef<'parent>
{
    pub fn new(extractor_map: &'parent ExtractorMap,
               dynamic_extractor_map: &'parent DynamicExtractorMap,
               cloc_tool: &'parent ClocHarness) -> Self {
        Self {
            extractor_map,
            dynamic_extractor_map,
            cloc_tool,
        }
    }

    /// processes a collection of package specs. Each package gets cloned, statically extracted, and
    /// dynamically extracted if possible. Results from all packages are collected and returned
    pub fn process_packages<'pkg, PackagesT>(
        &self,
        package_specs: PackagesT,
        extract_args: &ExtractArgs
    ) -> Result<HashMap<&'pkg PackageSpec, ProcessingResult<ExtractionResults>>, Box<dyn Error + 'static>>
        where PackagesT: Iterator<Item=&'pkg PackageSpec>
    {
        /*
        2.1: Clone package or fetch from existing location
        2.2: static extraction
        2.2.1: Extract files to submit
        2.2.2: submit files to server, collect results
        2.3: dynamic extraction
        2.3.1: turn off linting
        2.3.2: orchestrate files with monkey-patched regexes
        2.3.3: npm install
        2.3.4: run test suite
        2.3.5: combine usages
        2.4: filter usage results by what we extracted
        */

        let mut results: HashMap<&'pkg PackageSpec, ProcessingResult<ExtractionResults>> = HashMap::new();
        for spec in package_specs {
            trace!("package spec:\n{:?}", spec);
            // clone the package
            info!("Cloning or fetching repo {}", spec.repo());
            // this guard ensures that the package will always be removed when this object gets destroyed
            let package_path_guard = match clone_or_get_repo(spec, &extract_args.clone_base_path()) {
                Ok(path) => {
                    info!("Successfully cloned repo {}", spec.repo());
                    CleanUpRepoGuard::new(path)
                        .with_cleanup(extract_args.cleanup())
                }
                Err(err) => {
                    error!("Error while cloning repo: {}", err);
                    results.insert(spec, ProcessingResult::CloneFailed(err));
                    continue;
                }
            };

            let extraction_result = self.process_package_dir(spec, &package_path_guard, extract_args)?;
            info!("Finished extracting project '{}': {}", spec.name(), extraction_result);
            results.insert(spec, extraction_result);
        }

        Ok(results)
    }

    /// like process_packages, except results get published to the result sink on demand instead of
    /// collecting all results and sending them then
    pub fn process_packages_incremental<PackagesT>(
        &self,
        package_specs: PackagesT,
        extract_args: &ExtractArgs,
        db_client: &mut RegexDBClient,
        processing_report: &mut ProcessingReport,
    ) -> Result<(), Box<dyn Error + 'static>>
        where PackagesT: IntoIterator<Item=(PackageSpec, Vec<PackageSpec>)>
    {
        for (spec, dependents) in package_specs {
            trace!("package spec:\n{:?}", spec);
            // clone the package
            info!("Cloning or fetching repo {}", spec.repo());
            // this guard ensures that the package will always be removed when this object gets destroyed
            let package_path_guard = match clone_or_get_repo(&spec, &extract_args.clone_base_path()) {
                Ok(path) => {
                    info!("Successfully cloned repo {}", spec.repo());
                    CleanUpRepoGuard::new(path)
                        .with_cleanup(extract_args.cleanup())
                }
                Err(err) => {
                    error!("Error while cloning repo: {}", err);
                    save_package_execution(db_client, processing_report, spec, dependents, ProcessingResult::CloneFailed(err))?;
                    continue;
                }
            };

            let extraction_result = self.process_package_dir(&spec, &package_path_guard, extract_args)?;
            info!("Finished extracting project '{}': {}", spec.name(), extraction_result);
            save_package_execution(db_client, processing_report, spec, dependents, extraction_result)?;
        }

        Ok(())
    }

    /// processes a package that has been cloned. This does the actual steps of static and dynamic
    /// extraction. It is called internally by process_packages
    pub fn process_package_dir<ArgsT>(
        &self,
        package_spec: &PackageSpec,
        package_dir: &Path,
        _args: &ArgsT
    ) -> Result<ProcessingResult<ExtractionResults>, Box<dyn Error + 'static>>
        where ArgsT: ProvidesCommonExtractArgs
    {

        // get cloc info
        let loc_info = match self.cloc_tool.evaluate_directory(package_dir, package_spec.language()) {
            Ok(info) => {
                info!("successfully retrieved cloc info");
                Some(info)
            }
            Err(err) => match err {
                ClocError::TimedOut => {
                    // if we timed out, then we can't really make any assertions about what's in the
                    // project. So, leave it as optional
                    info!("cloc timed out. assuming that project has source, but not saving any loc info");
                    None
                }
                // otherwise, these conditions are actual errors that can't really be handled, so
                // propagate them up
                ClocError::LanguageNotFound => {
                    return Ok(ProcessingResult::LanguageNotFound);
                }
                other => {
                    error!("Error while evaluating cloc on project: {}", other);
                    return Err(other.into());
                }
            }
        };

        // statically extract regexes from package
        info!("Starting static extraction on package {}...", package_spec.name());
        let static_extract_result = static_extract_package(&package_spec, package_dir, &self.extractor_map);
        let Ok(static_regexes) = static_extract_result else {
            let static_error = static_extract_result.unwrap_err();
            error!(
                "error occurred while extracting static regexes: {}",
                &static_error,
            );

            return Ok(ProcessingResult::StaticExtractionError);
        };
        info!("static extraction got {} regexes", static_regexes.len());

        let processing_result = if let Some(dynamic_extractor) = self.dynamic_extractor_map.get(package_spec.language()) {
            info!("Starting to extract dynamic regexes for {}...", package_spec.name());
            let dynamic_extract_result = extract_dynamic_usages(
                package_spec,
                package_dir,
                dynamic_extractor.as_ref()
            );

            let Ok(result) = dynamic_extract_result else {
                error!(
                    "error occurred while extracting dynamic usages: {}",
                    dynamic_extract_result.unwrap_err()
                );
                return Ok(ProcessingResult::DynamicExtractorFailed);
            };

            match result {
                ProcessingResult::Partial { results, error } => {
                    let total_results = ExtractionResults::new(static_regexes, results, loc_info);
                    ProcessingResult::Partial {
                        results: total_results,
                        error: error.change_type().into(),
                    }
                }
                ProcessingResult::Okay(usages) => {
                    let total_results = ExtractionResults::new(static_regexes, usages, loc_info);
                    ProcessingResult::Okay(total_results)
                }
                other => other.change_type(),
            }
        } else {
            info!(
                "Package {} is not a JavaScript package, so no dynamic extraction",
                package_spec.name()
            );
            ProcessingResult::Okay(ExtractionResults::new(static_regexes, vec![], loc_info))
        };

        Ok(processing_result)
    }
}
