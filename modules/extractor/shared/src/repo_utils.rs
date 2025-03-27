use crate::error::ExtractorError;
use crate::package_spec::PackageSpec;
use log::{debug, error};
use std::path::{Path, PathBuf};
use subprocess::{Exec, ExitStatus, NullFile, Redirection};

/// Either clones the given package into TMP, or finds it in TMP if it has already been cloned
/// Params:
///     `package_spec` - The package we want to clone
///     `base_dir` - The path we want to clone into
/// Returns: A path to the package we just cloned, or an error
pub fn clone_or_get_repo(
    package_spec: &PackageSpec,
    base_dir: &Path,
) -> Result<PathBuf, ExtractorError> {
    // figure out what the path should be
    let base_dir_abs = base_dir
        .canonicalize()
        .map_err(|err| ExtractorError::Other(err.to_string()))?;
    let expected_package_path = PathBuf::from(format!(
        "{}/{}",
        base_dir_abs
            .to_str()
            .expect("Path should always be available"),
        clean_name(package_spec.name())
    ));

    if expected_package_path.exists() {
        return Ok(expected_package_path);
    }

    // we need to clone
    let clone_cmd = Exec::cmd("git")
        .arg("clone")
        .arg("--depth")
        .arg("1")
        .arg(package_spec.repo())
        .arg(&expected_package_path)
        // turn off prompts
        .env("GIT_TERMINAL_PROMPT", "0")
        .stdout(NullFile)
        .stderr(Redirection::Merge);

    let cmdline_str = clone_cmd.to_cmdline_lossy();

    let clone_status = clone_cmd.join().map_err(|err| ExtractorError::from(err))?;

    if !clone_status.success() {
        let return_status = match clone_status {
            ExitStatus::Exited(code) => Err(ExtractorError::SubCommandExited {
                exit_code: code,
                cmd: cmdline_str,
            }),
            ExitStatus::Signaled(signal) => Err(ExtractorError::SubCommandSignaled {
                exit_signal: signal,
                cmd: cmdline_str,
            }),
            _ => Err(ExtractorError::Other(
                "Unknown error while executing subprocess".to_string(),
            )),
        };

        // if the package is partially cleaned up, remove it
        if expected_package_path.exists() {
            match std::fs::remove_dir_all(&expected_package_path) {
                Ok(_) => debug!(
                    "Successfully cleaned up partially cloned path {}",
                    expected_package_path.to_string_lossy()
                ),
                Err(err) => error!(
                    "error while cleaning up partially cloned path '{}': {}",
                    expected_package_path.to_string_lossy(),
                    err
                ),
            }
        }

        return return_status;
    }

    Ok(expected_package_path)
}

/// Deletes a repository in its entirety
/// Params:
///     `path` - Base path of the repository
pub fn clean_up_repo(repo_path: &Path) -> Result<(), ExtractorError> {
    std::fs::remove_dir_all(repo_path).map_err(|err| ExtractorError::IO {
        source: err,
        operation: format!("removing repository {}", repo_path.to_str().unwrap()),
    })
}

pub fn get_last_commit(repo_path: &Path) -> Result<String, ExtractorError> {
    Exec::cmd("git")
        .arg("rev-parse")
        .arg("HEAD")
        .cwd(repo_path)
        .stdout(Redirection::Pipe)
        .capture()
        .map_err(|err| ExtractorError::from(err))
        .map(|data| data.stdout_str().trim().to_string())
}

/// removes any special characters in a project name for the directory
/// `@project.name/something` gets turned into `project-name-something`
fn clean_name(project_name: &str) -> String {
    let mut fixed_up = project_name.replace("@/.", "-");
    if fixed_up.chars().nth(0).is_some_and(|first_ch| first_ch == '-') {
        fixed_up.remove(0);
        fixed_up
    } else {
        fixed_up
    }
}
