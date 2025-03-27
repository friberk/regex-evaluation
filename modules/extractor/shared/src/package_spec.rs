use std::error::Error;
use std::fmt::{Display, Formatter};
use std::fs::File;
use std::io::{BufRead, BufReader};
use std::path::Path;
use std::str::FromStr;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, Eq, PartialEq, Hash)]
pub enum SourceLanguage {
    JAVASCRIPT,
    JAVA,
    PYTHON
}

impl Display for SourceLanguage {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        match self {
            SourceLanguage::JAVASCRIPT => write!(f, "javascript"),
            SourceLanguage::JAVA => write!(f, "java"),
            SourceLanguage::PYTHON => write!(f, "python")
        }
    }
}

impl FromStr for SourceLanguage {
    type Err = ();

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s {
            "JAVASCRIPT" => Ok(SourceLanguage::JAVASCRIPT),
            "JAVA" => Ok(SourceLanguage::JAVA),
            "PYTHON" => Ok(SourceLanguage::PYTHON),
            _ => Err(())
        }
    }
}

/// Represents a source package. Holds metadata like name, the URL to the GitHub repo, license,
/// language, and more. This structure is used heavily throughout the extraction process.
#[derive(Debug, Clone, Serialize, Deserialize, Eq, PartialEq, Hash)]
pub struct PackageSpec {
    name: String,
    repo: String,
    license: String,
    language: SourceLanguage,
    downloads: usize,
}

impl PackageSpec {

    pub fn new(name: String, repo: String, license: String, language: SourceLanguage, star_count: usize) -> Self {
        Self { name, repo, license, language, downloads: star_count }
    }

    pub fn local(name: String, source_language: SourceLanguage, path: &Path) -> Self {
        Self {
            name,
            language: source_language,
            repo: path.to_string_lossy().to_string(),
            license: String::default(),
            downloads: 0
        }
    }
    
    pub fn name(&self) -> &str {
        &self.name
    }
    pub fn repo(&self) -> &str {
        &self.repo
    }
    pub fn license(&self) -> &str {
        &self.license
    }
    pub fn language(&self) -> &SourceLanguage {
        &self.language
    }
    pub fn downloads(&self) -> usize {
        self.downloads
    }
    
    pub fn take_repo(self) -> String { self.repo }
}

/// Read many package specs from an input. Assumes that each line contains a file, and each line is
/// an NDJSON object
pub fn read_many_from_file(path: &Path) -> Result<Vec<PackageSpec>, Box<dyn Error + 'static>> {
    let file = File::open(path)?;
    let reader = BufReader::new(file);
    let mut specs: Vec<PackageSpec> = Vec::new();
    for line in reader.lines() {
        let line = line?;
        let trimmed = line.trim();
        if trimmed.is_empty() {
            continue;
        }
        let spec: PackageSpec = serde_json::from_str(trimmed)?;
        specs.push(spec);
    }
    
    Ok(specs)
}
