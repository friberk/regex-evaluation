use std::collections::HashMap;
use std::error::Error;
use std::path::{Path};
use std::sync::{Arc, Mutex};
use shared::error::ExtractorError;
use shared::package_spec::SourceLanguage;
use crate::extractor::extractor_info::ExtractorInfo;
use crate::extractor::manager::ExtractorManager;

pub mod manager;
pub mod extractor_info;
pub mod connection;

pub type ExtractorMap = HashMap<SourceLanguage, ExtractorManager>;

/// creates a map of extractors categorized by source language type
pub fn create_extractor_map<ExtractorInfoIterT: IntoIterator<Item=ExtractorInfo>>(
    extractor_infos: ExtractorInfoIterT,
    show_output: bool,
    extractor_logs_dir: Option<&Path>,
) -> Result<ExtractorMap, Box<dyn Error>> {
    // first, categorize into unique languages. Only take the last
    let extractor_info_map = extractor_infos.into_iter()
        .map(|extractor| (extractor.source_language().clone(), extractor))
        .collect::<HashMap<_, _>>();

    let mut map = ExtractorMap::with_capacity(extractor_info_map.len());
    for (lang, extractor_info) in extractor_info_map {
        let extractor_info_name = String::from(extractor_info.name());
        let manager = match ExtractorManager::new(extractor_info, show_output, extractor_logs_dir) {
            Ok(manager) => manager,
            Err(err) => {
                let err = ExtractorError::StartUp { name: extractor_info_name, cause: err };
                return Err(err.into());
            }
        };
        map.insert(lang, manager);
    }
    
    Ok(map)
}

/// creates a thread-safe global extractor map. Basically an arc<mutex> of the map.
pub fn create_global_extractor_map<ExtractorInfoIterT: IntoIterator<Item=ExtractorInfo>>(
    extractor_infos: ExtractorInfoIterT,
    show_output: bool,
    extractor_logs_dir: Option<&Path>,
) -> Result<Arc<Mutex<ExtractorMap>>, Box<dyn Error>> {
    let map = create_extractor_map(extractor_infos, show_output, extractor_logs_dir)?;
    Ok(Arc::new(Mutex::new(map)))
}
