pub mod js;
mod utils;
pub mod config;
pub mod java;

use std::collections::HashMap;
use std::error::Error;
use std::path::Path;
use shared::package_spec::{PackageSpec, SourceLanguage};
use shared::processing_result::ProcessingResult;

pub trait DynamicExtractorManager {
    fn pre_install(&self, package_spec: &PackageSpec, project_path: &Path) -> Result<ProcessingResult<()>, Box<dyn Error>>;
    fn install_deps(&self, package_spec: &PackageSpec, project_path: &Path) -> Result<ProcessingResult<()>, Box<dyn Error>>;
    fn build_pkg(&self, package_spec: &PackageSpec, project_path: &Path) -> Result<(), Box<dyn Error>>;
    fn run_test_suite(&self, package_spec: &PackageSpec, project_path: &Path, collect_examples_path: &Path) -> Result<ProcessingResult<()>, Box<dyn Error>>;
    fn example_limit(&self) -> Option<u32>;
}

/// Describes a map of dynamic extractors
pub type DynamicExtractorMap = HashMap<SourceLanguage, Box<dyn DynamicExtractorManager>>;
