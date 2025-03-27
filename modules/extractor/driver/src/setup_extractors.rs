use std::collections::HashMap;
use std::error::Error;
use std::ops::{RangeInclusive};
use std::path::{Path, PathBuf};
use log::{debug, log_enabled, warn};
use log::Level::Debug;
use rand::Rng;
use dynamic_extraction::dynamic_extractor_manager::DynamicExtractorMap;
use dynamic_extraction::dynamic_extractor_manager::java::java_home_config::JavaHomes;
use dynamic_extraction::dynamic_extractor_manager::java::MavenDynamicExtractor;
use dynamic_extraction::dynamic_extractor_manager::js::JavaScriptDynamicExtractor;
use shared::error::ExtractorError;
use shared::package_spec::SourceLanguage;
use static_extraction::extractor::{create_extractor_map, ExtractorMap};
use static_extraction::extractor::extractor_info::{ExtractorInfo, ExtractorServerConnectionInfo};
use crate::args::{CommonExtractArgs};

/// Used to set up static extractors used during the extraction process. This tool allows us to 
/// configure which static extractors we want to start, and then automates starting all of them.
pub struct ExtractorMapBuilder<'a> {
    args: &'a CommonExtractArgs,
    extractors: HashMap<SourceLanguage, ExtractorInfo>
}

impl<'a> ExtractorMapBuilder<'a> {
    
    /// Creates a new instance. Doesn't have any side effects
    pub fn new(args: &'a CommonExtractArgs) -> Self {
        Self {
            args,
            extractors: HashMap::default()
        }
    }
    
    /// Use this to start all languages
    pub fn with_all(self) -> Self {
        self
            .with_lang(SourceLanguage::JAVASCRIPT)
            .with_lang(SourceLanguage::JAVA)
            .with_lang(SourceLanguage::PYTHON)
    }
    
    /// Choose a specific language to start.
    pub fn with_lang(mut self, lang: SourceLanguage) -> Self {
        match lang {
            SourceLanguage::JAVASCRIPT => {
                self.extractors.insert(lang, js_extractor_info(self.args.js_extractor_path()));
            }
            SourceLanguage::JAVA => {
                self.extractors.insert(lang, java_extractor_info(self.args.java_extractor_path()));
            }
            SourceLanguage::PYTHON => {
                self.extractors.insert(lang, python_v2_extractor_info(self.args.python_extractor_path()));
            }
        }
        
        self
    }

    /// Actually start all extractors. This should always be called last. This is the function that
    /// actually starts all static extractors.
    pub fn setup_extractor_map(self) -> Result<ExtractorMap, Box<dyn Error>> {
        
        let map = create_extractor_map(self.extractors.into_values(), self.args.show_extractor_output(), self.args.extractor_logs_dir().as_ref().map(PathBuf::as_path))?;

        const RETRY_LIMIT: usize = 10;
        let mut retries = 0;
        while retries < RETRY_LIMIT {
            let mut any_extractor_failed = false;
            for (_, extractor) in &map {
                if let Some(err) = extractor.test_connection() {
                    warn!("Extractor {} is not up yet. Test connection failed with '{}'. Retrying...", err, extractor.extractor_info().name());
                    any_extractor_failed = true;
                }
            }

            if !any_extractor_failed {
                break;
            }

            retries += 1;
        }

        if retries >= RETRY_LIMIT {
            return Err(ExtractorError::Other("Failed to get all extractors on line".to_string()).into());
        }

        Ok(map)
    }
}

#[inline]
fn js_extractor_info(extractor_path: &Path) -> ExtractorInfo {
    ExtractorInfo::interpreted("node", extractor_path, "js-parser", ExtractorServerConnectionInfo::Unix(pid_listening_path("js-parser")), 1, SourceLanguage::JAVASCRIPT)
}

#[inline]
fn java_extractor_info(extractor_path: &Path) -> ExtractorInfo {
    ExtractorInfo::binary(extractor_path, "java-parser", ExtractorServerConnectionInfo::Tcp(random_port_between(8910..=9910)), 1, SourceLanguage::JAVA)
}

#[inline]
fn python_extractor_info(extractor_path: &Path) -> ExtractorInfo {
    ExtractorInfo::interpreted("python3", extractor_path, "py-parser", ExtractorServerConnectionInfo::Unix(pid_listening_path("py-parser")), 1, SourceLanguage::PYTHON)
}

#[inline]
fn python_v2_extractor_info(extractor_path: &Path) -> ExtractorInfo {
    ExtractorInfo::binary(
        extractor_path,
        "py-parser-v2",
        ExtractorServerConnectionInfo::Unix(pid_listening_path("py-parser-v2")),
        1,
        SourceLanguage::PYTHON
    )
}

/// pick a random port between two bounds
fn random_port_between(range: RangeInclusive<u16>) -> u16 {
    let t_rng = &mut rand::thread_rng();
    t_rng.gen_range(range)
}

fn pid_listening_path(name: &str) -> PathBuf {
    let root = std::env::temp_dir();
    let pid = std::process::id();
    let name = format!("{}-{}.sock", name, pid);

    root.join(name)
}


/// build a map of dynamic extractors
pub fn build_dynamic_extractor_map(common_args: &CommonExtractArgs) -> DynamicExtractorMap {
    
    // configure java homes
    let java_homes = JavaHomes::search(["/usr/lib/jvm"]).unwrap_or_else(|error| {
        warn!("error while searching for java homes: {}", error);
        JavaHomes::nop()
    });

    if log_enabled!(Debug) {
        let java_versions = java_homes.found_java_versions().map(ToString::to_string).collect::<Vec<_>>().join(", ");
        debug!("Found java versions {}", java_versions);
    }
    
    let js_dynamic_extractor = JavaScriptDynamicExtractor::from(common_args.js_dynamic_args());
    let mvn_dynamic_extractor = MavenDynamicExtractor::from(common_args.maven_dynamic_args(java_homes));

    let mut map = DynamicExtractorMap::new();
    map.insert(SourceLanguage::JAVASCRIPT, Box::new(js_dynamic_extractor));
    map.insert(SourceLanguage::JAVA, Box::new(mvn_dynamic_extractor));

    map
}
