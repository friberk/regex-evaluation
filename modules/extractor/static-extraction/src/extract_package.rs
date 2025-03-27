use std::error::Error;
use std::path::Path;
use std::time::Duration;
use log::{debug, warn};
use shared::package_spec::{PackageSpec, SourceLanguage};
use shared::regex_entity::RegexEntity;
use shared::repo_utils::{get_last_commit};
use shared::traverser::{create_java_traverser, create_js_traverser, create_python_traverser};
use crate::extractor::ExtractorMap;

/// Takes a package spec and extracts all regexes statically
pub fn static_extract_package(package_spec: &PackageSpec, package_path: &Path, extractor_map: &ExtractorMap) -> Result<Vec<RegexEntity>, Box<dyn Error>> {
    // get the extractor manager we want
    let Some(extractor_manager) = extractor_map.get(package_spec.language()) else {
        warn!("Unsupported source language {:?}. Skipping...", package_spec.language());
        return Ok(Vec::default());
    };
    
    // create a connection
    debug!("Connecting to extractor {}", extractor_manager.extractor_info().name());
    let mut connection = extractor_manager.create_connection()?;
    debug!("Successfully connected to extractor {}", extractor_manager.extractor_info().name());
    connection.set_read_timeout(Duration::from_secs(60 * 5)).expect("Setting duration should not fail");
    
    let traverser = match package_spec.language() {
        SourceLanguage::JAVASCRIPT => create_js_traverser(&package_path),
        SourceLanguage::JAVA => create_java_traverser(&package_path),
        SourceLanguage::PYTHON => create_python_traverser(&package_path)
    };
    
    for entry in traverser {
        let abs_path = entry.path().canonicalize()?;
        debug!("Sending path {}", abs_path.to_string_lossy());
        connection.send_path(&abs_path)?;
    }
    
    connection.send_done()?;

    debug!("Receiving results...");
    let results = connection.recv_response()?;
    debug!("Got {} results", results.len());
    
    // get the last commit
    let last_commit = get_last_commit(&package_path)?;
    
    let entities = results.into_iter()
        .map(|entry| RegexEntity::from_parsed(entry, package_spec, &last_commit, package_path))
        .collect::<Vec<_>>();
    
    Ok(entities)
}
