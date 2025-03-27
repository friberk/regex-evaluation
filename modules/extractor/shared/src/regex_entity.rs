use std::path::{Path, PathBuf};
use serde::{Deserialize, Serialize};
use crate::package_spec::PackageSpec;

/// Represents a regex entity as produced from the static extractors. This should not be used in
/// most cases. It's just a convenience intermediate structure for interacting with the static
/// extractors.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParsedRegexEntity {
    pattern: String,
    flags: String,
    line_no: usize,
    source_file: String,
}

impl ParsedRegexEntity {
    pub fn new<StrT: Into<String>>(pattern: StrT, flags: StrT, line_no: usize, source_file: StrT) -> Self {
        Self {
            pattern: pattern.into(),
            flags: flags.into(),
            line_no,
            source_file: source_file.into()
        }
    }
}

/// Represents a full regex entity. This should be used in most cases.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RegexEntity {
    pattern: String,
    flags: String,
    line_no: usize,
    source_file: String,
    repo_location: String,
    license: String,
    commit: String,
}

impl RegexEntity {
    pub fn from_parsed(parsed_regex_entity: ParsedRegexEntity, package_spec: &PackageSpec, last_commit: &str, package_base_path: &Path) -> Self {

        // compute the path relative to the project base path
        let relative_source_path = PathBuf::from(parsed_regex_entity.source_file)
            .strip_prefix(package_base_path).expect("Stripping prefix should not fail")
            .to_path_buf();

        Self {
            pattern: parsed_regex_entity.pattern,
            flags: parsed_regex_entity.flags,
            line_no: parsed_regex_entity.line_no,
            source_file: relative_source_path.to_string_lossy().to_string(),
            repo_location: package_spec.repo().to_string(),
            license: package_spec.license().to_string(),
            commit: last_commit.to_string(),
        }
    }
    
    pub fn pattern(&self) -> &str {
        &self.pattern
    }
    pub fn flags(&self) -> &str {
        &self.flags
    }
    pub fn line_no(&self) -> usize {
        self.line_no
    }
    pub fn source_file(&self) -> &str {
        &self.source_file
    }
    pub fn repo_location(&self) -> &str {
        &self.repo_location
    }
    pub fn license(&self) -> &str {
        &self.license
    }
    pub fn commit(&self) -> &str {
        &self.commit
    }
}
