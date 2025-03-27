use std::collections::{BTreeMap};
use std::path::{Path, PathBuf};
use log::{debug, warn};
use subprocess::Exec;
use crate::dynamic_extractor_manager::java::version_info::{parse_java_home_version, parse_java_version};

/// Represents a set of possible java home directories
pub struct JavaHomes {
    home_paths: BTreeMap<u8, PathBuf>,
}

impl JavaHomes {
    
    /// Constructs a NOP java homes configurerer. Basically, it'll never configure the JAVA_HOME
    /// env variable, effectively making it NOP
    pub fn nop() -> Self {
        Self {
            home_paths: BTreeMap::default(),
        }
    }
    
    pub fn search<IterT, ItemT>(search_paths: IterT) -> std::io::Result<Self>
    where ItemT: Into<PathBuf>,
          IterT: IntoIterator<Item=ItemT>
    {
        let mut homes = BTreeMap::<u8, PathBuf>::new();

        // iterate over each search path and look for potential java homes
        for search_path in search_paths.into_iter().map(Into::into) {
            for entry in std::fs::read_dir(&search_path)? {
                let Ok(entry) = entry else {
                    warn!("while finding java homes, entry failed: {}", entry.unwrap_err());
                    continue;
                };

                let Ok(entry_file_type) = entry.file_type() else {
                    warn!("could not fetch entry's file type");
                    continue;
                };

                // skip anything that isn't a directory or symlink
                if !(entry_file_type.is_dir() || entry_file_type.is_symlink()) {
                    debug!("entry {} is not a directory or link to directory, skipping", entry.path().to_string_lossy());
                    continue;
                }

                // get either the directory or the link for the directory
                let java_home = if entry_file_type.is_symlink() {
                    let linked_dir = std::fs::read_link(entry.path())?;
                    if linked_dir.is_absolute() {
                        linked_dir
                    } else {
                        search_path.join(linked_dir)
                    }
                } else {
                    // implicitly dir
                    search_path.join(entry.path())
                };

                debug!("got java home: {}", java_home.to_string_lossy());
                let java_home = java_home.canonicalize().expect("Canonicalization of an existing directory should not fail");
                debug!("absolute java home: {}", java_home.to_string_lossy());

                // figure out what version the directory is for
                let Some(java_home_version) = parse_java_home_version(entry.file_name().to_string_lossy().as_ref()) else {
                    warn!("failed to parse version for {}, so skipping", entry.path().to_string_lossy());
                    continue;
                };
                
                homes.insert(java_home_version, java_home);
            }
        }

        Ok(Self {
            home_paths: homes
        })
    }
    
    /// determines if the requested java version string is found in the java homes configuration
    pub fn has_java_version(&self, version_str: &str) -> bool {
        parse_java_version(version_str)
            .map(|version| self.home_paths.contains_key(&version))
            .unwrap_or(false)
    }
    
    /// attempts to configure a command's java home variable based on the given version string.
    /// if there is no corresponding version, then the command will be returned unchanged
    pub fn configure_java_home_env<StrT: AsRef<str>>(&self, exec: Exec, version_str: StrT) -> Exec {
        if let Some(java_home) = self.get_home_for_version(version_str) {
            exec.env("JAVA_HOME", java_home)
        } else {
            exec
        }
    }
    
    /// return the versions we have found
    pub fn found_java_versions(&self) -> impl Iterator<Item=&u8> {
        self.home_paths.keys()
    }
    
    /// given some string describing a java version, try to find a java home to work with it
    fn get_home_for_version<StrT: AsRef<str>>(&self, version_str: StrT) -> Option<&Path> {
        let version = parse_java_version(version_str.as_ref())?;
        self.home_paths.get(&version).map(|pb| pb.as_path())
    }
}
