use std::path::PathBuf;
use shared::package_spec::SourceLanguage;

#[derive(Clone)]
pub enum ExtractorServerConnectionInfo {
    /// a path to serve on
    Unix(PathBuf),
    /// a port to serve on
    Tcp(u16)
}

impl Into<String> for ExtractorServerConnectionInfo {
    fn into(self) -> String {
        match self {
            ExtractorServerConnectionInfo::Unix(path) => path.to_str().unwrap().to_string(),
            ExtractorServerConnectionInfo::Tcp(port) => format!("{}", port),
        }
    }
}

/// Metadata to specify how to start a static extractor process. These shouldn't be used very often
pub struct ExtractorInfo {
    /// the command used to execute the extractor. If none, then the extractor is native
    executing_command: Option<String>,
    /// the path to the extractor
    extractor_path: PathBuf,
    /// the name of the extractor
    name: String,
    /// info on how to connect
    connection_info: ExtractorServerConnectionInfo,
    /// how many workers to execute with
    workers: usize,
    /// which language is supported by this extractor
    source_language: SourceLanguage,
}

impl ExtractorInfo {
    pub fn interpreted<StrT: Into<String>, PathT: Into<PathBuf>>(executing_command: StrT, extractor_path: PathT, name: StrT, connection_info: ExtractorServerConnectionInfo, workers: usize, source_language: SourceLanguage) -> Self {
        Self {
            executing_command: Some(executing_command.into()),
            extractor_path: extractor_path.into(),
            name: name.into(),
            connection_info,
            workers,
            source_language
        }
    }
    
    pub fn binary<StrT: Into<String>, PathT: Into<PathBuf>>(extractor_path: PathT, name: StrT, connection_info: ExtractorServerConnectionInfo, workers: usize, source_language: SourceLanguage) -> Self {
        Self {
            executing_command: None,
            extractor_path: extractor_path.into(),
            name: name.into(),
            connection_info,
            workers,
            source_language
        }
    }

    pub fn executing_command(&self) -> Option<&String> {
        self.executing_command.as_ref()
    }
    pub fn extractor_path(&self) -> &PathBuf {
        &self.extractor_path
    }
    pub fn name(&self) -> &str {
        &self.name
    }
    pub fn connection_info(&self) -> &ExtractorServerConnectionInfo {
        &self.connection_info
    }
    pub fn workers(&self) -> usize {
        self.workers
    }
    pub fn source_language(&self) -> &SourceLanguage {
        &self.source_language
    }
}
