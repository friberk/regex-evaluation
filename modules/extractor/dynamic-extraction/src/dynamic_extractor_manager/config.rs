use std::path::{Path, PathBuf};
use crate::custom_node_args::CustomNodeArgs;
use crate::dynamic_extractor_manager::java::java_home_config::JavaHomes;

/// Struct for passing arguments to the dynamic extractor
pub struct JsDynamicExtractorConfig<'args> {
    pub js_monkeypatch_path: &'args Path,
    pub custom_node_args: Option<CustomNodeArgs>,
    pub collect_stack_traces: bool,
    pub example_limit: Option<u32>,
    pub fake_home: Option<&'args Path>,
    pub install_duration: std::time::Duration,
    pub test_duration: std::time::Duration,
}

pub struct MavenDynamicExtractorConfig {
    pub jde_agent_path: PathBuf,
    pub example_limit: Option<u32>,
    pub install_duration: std::time::Duration,
    pub test_duration: std::time::Duration,
    pub java_home_config: JavaHomes,
    pub fake_home: Option<PathBuf>,
    pub local_install_path: Option<PathBuf>,
    pub clean_env: bool,
}
