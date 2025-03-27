use std::ops::Deref;
use std::path::{Path, PathBuf};
use log::{error, info};
use crate::repo_utils::clean_up_repo;

/// A RAII wrapper around a file or directory. This guard wraps a path. When the guard falls out of
/// scope, it will delete the directory if `cleanup` mode is set. The purpose of this guard is to
/// ensure that filesystem resources are freed. This guard can also behave as a [Path](std::path::Path).
pub struct CleanUpRepoGuard {
    repo: PathBuf,
    cleanup: bool,
}

impl CleanUpRepoGuard {
    
    /// creates a new guard on the given path. `cleanup` is set to true by default.
    pub fn new<PathT: Into<PathBuf>>(path: PathT) -> Self {
        Self {
            cleanup: true,
            repo: path.into()
        }
    }

    /// optionally turn off resource reclamation
    pub fn with_cleanup(mut self, cleanup: bool) -> Self {
        self.cleanup = cleanup;
        self
    }
    
    pub fn repo_path(&self) -> &Path {
        &self.repo
    }

    fn exists(&self) -> bool {
        self.repo.try_exists().unwrap_or_else(|err| {
            error!("error while checking if repo exists: {}", err);
            false
        })
    }
}

impl AsRef<Path> for CleanUpRepoGuard {
    fn as_ref(&self) -> &Path {
        self.repo_path()
    }
}

impl Deref for CleanUpRepoGuard {
    type Target = Path;

    fn deref(&self) -> &Self::Target {
        self.repo_path()
    }
}

impl Drop for CleanUpRepoGuard {
    fn drop(&mut self) {
        if self.exists() && self.cleanup {
            match clean_up_repo(&self.repo) {
                Ok(_) => info!("successfully cleaned up path: {}", self.repo.to_string_lossy()),
                Err(err) => error!("error occurred while cleaning up repository: {}", err),
            }
        }
    }
}
