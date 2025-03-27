use std::cell::RefCell;
use std::path::PathBuf;

use subprocess::Exec;

pub struct FakeHomeConfigurer {
    fake_home_path: PathBuf,
    canonical_path_cache: RefCell<Option<PathBuf>>
}

impl FakeHomeConfigurer {
    pub fn new<PathT: Into<PathBuf>>(path: PathT) -> Self {
        Self {
            fake_home_path: path.into(),
            canonical_path_cache: RefCell::new(None)
        }
    }

    /// Configure a command to set a fake home environment variable
    pub fn configure_command(&self, command: Exec) -> std::io::Result<Exec> {
        let path = self.get_or_create()?;
        Ok(command.env("HOME", path))
    }

    fn get_or_create(&self) -> std::io::Result<PathBuf> {
        // check our cache
        if let Some(canonical_path) = self.canonical_path_cache.take().as_ref() {
            return Ok(canonical_path.clone());
        }

        // try canonicalizing and creating path
        let dir_existance = self.fake_home_path.try_exists()?;
        if !dir_existance {
            std::fs::create_dir(&self.fake_home_path)?;
        }
        let full_path = self.fake_home_path.canonicalize()?;
        // once created, cache the result to signal that all of this has been done already
        self.canonical_path_cache.replace(Some(full_path.clone()));

        Ok(full_path)
    }
}

#[cfg(test)]
mod tests {
    use std::path::PathBuf;

    use shared::clean_up_guard::CleanUpRepoGuard;

    use crate::fake_home_config::FakeHomeConfigurer;

    #[test]
    fn canonicalize_fails_for_directory_that_doesnt_exist() {
        let path = PathBuf::from("/tmp/this-directory-doesnt-exist");
        path.canonicalize().expect_err("canonicalization shouldn't fail");
    }
    
    #[test]
    fn fake_home_configurer_works_when_directory_doesnt_exist() {
        let path = PathBuf::from("/tmp/this-directory-doesnt-exist");
        let repo_guard = CleanUpRepoGuard::new(path);
        let configurer = FakeHomeConfigurer::new(repo_guard.repo_path());
        let fake_home = configurer.get_or_create().expect("Creating fake directory should work");
        assert_eq!(fake_home.as_os_str(), "/tmp/this-directory-doesnt-exist");
    }
}
