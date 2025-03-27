pub mod java_home_config;
mod version_info;
mod pom_info;

use std::error::Error;
use std::path::{Path, PathBuf};
use std::time::Duration;
use log::{debug, error, info, warn};
use subprocess::{Exec, ExitStatus, NullFile};
use shared::error::ExtractorError;
use shared::package_spec::PackageSpec;
use shared::processing_result::ProcessingResult;
use shared::subprocess_utils::kill_and_reap_timed_process;
use crate::dynamic_extractor_manager::config::MavenDynamicExtractorConfig;
use crate::dynamic_extractor_manager::DynamicExtractorManager;
use crate::dynamic_extractor_manager::java::java_home_config::JavaHomes;
use crate::dynamic_extractor_manager::java::pom_info::{extract_pom_version, PomError};
use crate::dynamic_extractor_manager::utils::{clear_env_except_for_path};
use crate::fake_home_config::FakeHomeConfigurer;

pub struct MavenDynamicExtractor {
    jde_agent_path: PathBuf,
    java_homes: JavaHomes,
    example_limit: Option<u32>,
    install_timeout: Duration,
    test_timeout: Duration,
    fake_home_configurer: Option<FakeHomeConfigurer>,
    local_install_directory: Option<PathBuf>,
    clean_env: bool,
}

impl From<MavenDynamicExtractorConfig> for MavenDynamicExtractor {
    fn from(value: MavenDynamicExtractorConfig) -> Self {
        Self {
            jde_agent_path: value.jde_agent_path,
            java_homes: value.java_home_config,
            example_limit: value.example_limit,
            install_timeout: value.install_duration,
            test_timeout: value.test_duration,
            fake_home_configurer: value.fake_home.map(FakeHomeConfigurer::new),
            local_install_directory: value.local_install_path,
            clean_env: value.clean_env
        }
    }
}

impl MavenDynamicExtractor {
    /// look for a specified java version inside the POM
    fn find_specified_java_version(&self, project_path: &Path) -> std::io::Result<Option<String>> {
        let java_version_result = extract_pom_version(project_path.join("pom.xml").as_path());
        let version = match java_version_result {
            Ok(version_str) => {
                info!("pom specified java version {}", version_str);
                Some(version_str)
            }
            Err(err) => match err {
                PomError::IO(io_err) => {
                    error!("I/O error happened while trying to read pom");
                    return Err(io_err);
                }
                PomError::XmlSyntax(syntax_err) => {
                    warn!("XML syntax error occurred while looking for java version: {}", syntax_err);
                    warn!("Ignoring any specified version, defaulting to system default");
                    None
                }
                PomError::NoVersion => {
                    info!("no version provided. Using system default");
                    None
                }
                PomError::Other => {
                    info!("some other error occurred while looking for java version");
                    None
                }
            }
        };
        
        Ok(version)
    }

    fn configure_command_environment(&self, mut cmd: Exec, version_str: Option<String>) -> std::io::Result<Exec> {
        if self.clean_env {
            cmd = clear_env_except_for_path(cmd);
        }

        cmd = self.configure_java_home(cmd, version_str);
        cmd = self.configure_fake_home(cmd)?;
        Ok(cmd)
    }

    fn configure_java_home(&self, cmd: Exec, version_str: Option<String>) -> Exec {
        if let Some(specified_java_version) = version_str {
            if !self.java_homes.has_java_version(&specified_java_version) {
                warn!("The specified java version was not found while scanning. Leaving JAVA_HOME unconfigured");
            }

            self.java_homes.configure_java_home_env(cmd, &specified_java_version)
        } else {
            cmd
        }
    }
    
    fn configure_fake_home(&self, cmd: Exec) -> std::io::Result<Exec> {
        if let Some(fake_home) = self.fake_home_configurer.as_ref() {
            fake_home.configure_command(cmd)
        } else {
            Ok(cmd)
        }
    }

    fn configure_local_install(&self, cmd: Exec, project_path: &Path) -> Exec {
        let path = self.local_install_directory.clone().unwrap_or(self.default_local_install(project_path));
        cmd
            .arg("-D")
            .arg(format!("maven.repo.local={}", path.to_string_lossy()))
    }

    /// default path to use as local maven repo
    fn default_local_install(&self, project_path: &Path) -> PathBuf {
        project_path.join(".maven-install")
    }

    /// look for a maven wrapper and use that if it exists. Otherwise, default to normal maven
    fn find_maven_command(&self, project_path: &Path) -> Exec {
        let potential_maven_wrapper = project_path.join("mvnw");
        if potential_maven_wrapper.exists() {
            Exec::cmd(potential_maven_wrapper)
        } else {
            Exec::cmd("mvn")
        }
    }
}

impl DynamicExtractorManager for MavenDynamicExtractor {
    fn pre_install(&self, _package_spec: &PackageSpec, project_path: &Path) -> Result<ProcessingResult<()>, Box<dyn Error>> {
        // find a pom.xml file in the root of the project
        let pom_file_path = project_path.join("pom.xml");
        let pre_install_status = if pom_file_path.try_exists()? {
            ProcessingResult::Okay(())
        } else {
            // if it doesn't exist, we can't use this dynamic extractor
            ProcessingResult::UnsupportedBuildTool
        };

        // figure out if we have a supported version of java
        Ok(pre_install_status)
    }

    fn install_deps(&self, package_spec: &PackageSpec, project_path: &Path) -> Result<ProcessingResult<()>, Box<dyn Error>> {
        
        let specified_java_version = self.find_specified_java_version(project_path)?;

        // try to use a wrapper if available
        let mut install_cmd = self.find_maven_command(project_path);

        install_cmd = self.configure_local_install(install_cmd, project_path);
        info!("{}: local install configured", package_spec.name());

        install_cmd = install_cmd
            .arg("-q")
            .arg("clean")
            .arg("compile")
            .stdin(NullFile)
            .cwd(project_path);

        info!("{}: configuring install command environment", package_spec.name());
        install_cmd = self.configure_command_environment(install_cmd, specified_java_version)?;
        info!("{}: environment configured", package_spec.name());
        
        let cmd = install_cmd.to_cmdline_lossy();
        info!("running [{}] on in package {}", cmd, project_path.display());
        let mut install_handle = install_cmd
            .popen()?;

        let exit_status = install_handle
            .wait_timeout(self.install_timeout)?;

        // TODO dedup this...
        match exit_status {
            None => {
                kill_and_reap_timed_process(&mut install_handle, "timed out install/build");
                return Ok(ProcessingResult::InstallTimeout);
            },
            Some(status) => {
                if !status.success() {
                    let err = match status {
                        ExitStatus::Exited(code) => ExtractorError::SubCommandExited {
                            cmd,
                            exit_code: code,
                        },
                        ExitStatus::Signaled(signal) => ExtractorError::SubCommandSignaled {
                            cmd,
                            exit_signal: signal,
                        },
                        _ => ExtractorError::Other("unknown failure".to_string()),
                    };

                    Ok(ProcessingResult::InstallFailed(err))
                } else {
                    Ok(ProcessingResult::Okay(()))
                }
            }
        }
    }

    fn build_pkg(&self, _package_spec: &PackageSpec, _project_path: &Path) -> Result<(), Box<dyn Error>> {
        debug!("project is compiled during install, moving to test");
        Ok(())
    }

    fn run_test_suite(&self, package_spec: &PackageSpec, project_path: &Path, collect_examples_path: &Path) -> Result<ProcessingResult<()>, Box<dyn Error>> {

        // SUPER redundant to do this twice without anything changing...
        let specified_java_version = self.find_specified_java_version(project_path)?;
        
        let mut test_cmd = self.find_maven_command(project_path);
        test_cmd = self.configure_local_install(test_cmd, project_path);
        info!("{}: local install configured", package_spec.name());

        test_cmd = test_cmd
            .arg("-q")
            .arg(format!("-DargLine=\"-javaagent:{}\"", self.jde_agent_path.to_string_lossy()))
            .arg("verify")
            .stdin(NullFile)
            .cwd(project_path);

        info!("{}: configuring test command environment", package_spec.name());
        test_cmd = self.configure_command_environment(test_cmd, specified_java_version)?;
        test_cmd = test_cmd.env("DYN_EXTRACTOR_OUTPUT_PATH", collect_examples_path);
        info!("{}: environment configured", package_spec.name());
        
        let cmd = test_cmd.to_cmdline_lossy();
        info!("running test suite by executing [{}]", &cmd);

        let mut test_popen_handle = test_cmd
            .popen()?;

        let test_result = test_popen_handle
            .wait_timeout(self.test_timeout)?;

        // if test suite finished okay, then there's nothing to do
        if test_result.is_some_and(|status| status.success()) {
            return Ok(ProcessingResult::Okay(()))
        }
        
        // otherwise, we need to figure out an error case
        let result = if let Some(status) = test_result {
            let extractor_err = match status {
                ExitStatus::Exited(status) => ExtractorError::SubCommandExited {
                    exit_code: status,
                    cmd,
                },
                ExitStatus::Signaled(signal) => ExtractorError::SubCommandSignaled {
                    exit_signal: signal,
                    cmd,
                },
                _ => ExtractorError::Other(format!("Error while executing {}", cmd)),
            };

            ProcessingResult::TestFailed(extractor_err)
        } else {
            // we timed out -- kill the process and keep going
            kill_and_reap_timed_process(&mut test_popen_handle, "timed out test suite");
            ProcessingResult::TestTimeout
        };

        Ok(result)
    }

    fn example_limit(&self) -> Option<u32> {
        self.example_limit
    }
}
