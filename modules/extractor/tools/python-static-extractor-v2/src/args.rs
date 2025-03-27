use std::path::PathBuf;
use clap::Parser;

#[derive(Debug, Clone, Parser)]
pub struct Args {
    /// path to where the python static extractor is located
    #[arg(long, env = "PYTHON_STATIC_EXTRACTOR_MODULE_PATH")]
    pub extractor_path: PathBuf,
    /// where the server should listen on
    pub listen_path: PathBuf,
    /// how many workers to use
    pub worker_count: u32,
}
