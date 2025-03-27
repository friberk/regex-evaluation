use std::error::Error;
use std::io::Read;
use std::path::{Path, PathBuf};
use std::time::Duration;
use log::{info, trace, warn};
use subprocess::{Exec, ExitStatus, NullFile, Redirection};
use shared::clean_up_guard::CleanUpRepoGuard;
use shared::error::ExtractorError;
use shared::package_spec::PackageSpec;
use shared::processing_result::ProcessingResult;
use shared::subprocess_utils::kill_and_reap_timed_process;
use crate::custom_node_args::CustomNodeArgs;
use crate::dynamic_extractor_manager::config::JsDynamicExtractorConfig;
use crate::dynamic_extractor_manager::DynamicExtractorManager;
use crate::fake_home_config::FakeHomeConfigurer;
use crate::preprocess::preprocess_npm_project_directory;
use crate::regexp_monkey_patch::configure_monkey_patch_env;

pub struct JavaScriptDynamicExtractor {
    js_monkeypatch_path: PathBuf,
    custom_node_args: Option<CustomNodeArgs>,
    collect_stack_traces: bool,
    example_limit: Option<u32>,
    fake_home: Option<FakeHomeConfigurer>,
    install_timeout: Duration,
    test_timeout: Duration,
}

impl<'args> From<JsDynamicExtractorConfig<'args>> for JavaScriptDynamicExtractor {
    fn from(value: JsDynamicExtractorConfig<'args>) -> Self {
        Self {
            js_monkeypatch_path: value.js_monkeypatch_path.to_path_buf(),
            custom_node_args: value.custom_node_args,
            collect_stack_traces: value.collect_stack_traces,
            example_limit: value.example_limit,
            fake_home: value.fake_home.map(FakeHomeConfigurer::new),
            install_timeout: value.install_duration,
            test_timeout: value.test_duration,
        }
    }
}

impl JavaScriptDynamicExtractor {
    fn configure_home(&self, exec: Exec) -> std::io::Result<Exec> {
        if let Some(fake_home_configurer) = self.fake_home.as_ref() {
            fake_home_configurer.configure_command(exec)
        } else {
            Ok(exec)
        }
    }
}

impl DynamicExtractorManager for JavaScriptDynamicExtractor {
    fn pre_install(&self, package_spec: &PackageSpec, project_path: &Path) -> Result<ProcessingResult<()>, Box<dyn Error>> {
        info!("Starting to preprocess package {}", package_spec.name());
        preprocess_npm_project_directory(&project_path)?;
        info!("Successfully preprocessed package {}", package_spec.name());
        Ok(ProcessingResult::Okay(()))
    }

    fn install_deps(&self, package_spec: &PackageSpec, project_path: &Path) -> Result<ProcessingResult<()>, Box<dyn Error>> {
        let cache_dir = std::env::temp_dir().join(format!("npm-cache-dir-{}", std::process::id()));
        let cache_dir_guard = CleanUpRepoGuard::new(cache_dir);
        let mut install_cmd = Exec::cmd("npm")
            .arg("install")
            .arg("--cache")
            .arg(cache_dir_guard.repo_path())
            .stdin(NullFile)
            .cwd(project_path);

        // configure home directory
        info!("{}: configuring fake home...", package_spec.name());
        install_cmd = self.configure_home(install_cmd)?;
        info!("{}: fake home configured", package_spec.name());

        let cmd = install_cmd.to_cmdline_lossy();
        info!("running [{}] in package {}", cmd, project_path.to_string_lossy());
        let mut install_handle = install_cmd
            .popen()?;

        let exit_status = install_handle
            .wait_timeout(self.install_timeout)?;

        match exit_status {
            None => {
                kill_and_reap_timed_process(&mut install_handle, "timed out install");
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

    fn build_pkg(&self, package_spec: &PackageSpec, project_path: &Path) -> Result<(), Box<dyn Error>> {
        info!(
        "running [npm run build] on package {}",
        project_path.to_string_lossy()
    );
        let mut build_cmd = Exec::cmd("npm")
            .arg("run")
            .arg("build")
            .cwd(project_path);

        // configure fake home for build as well
        info!("{}: configuring fake home...", package_spec.name());
        build_cmd = self.configure_home(build_cmd)?;
        info!("{}: fake home configured", package_spec.name());

        let mut build_handle = build_cmd
            .popen()?;

        let build_exit_status = build_handle
            .wait_timeout(self.install_timeout)?;

        match build_exit_status {
            None => {
                kill_and_reap_timed_process(&mut build_handle, "timed out build");
                warn!("running [npm run build] timed out, but continuing anyways...");
            }
            Some(status) => if status.success() {
                info!("successfully ran [npm run build]")
            } else {
                warn!("running [npm ran build] failed, but continuing anyway");
            }
        }

        Ok(())
    }

    fn run_test_suite(&self, package_spec: &PackageSpec, project_path: &Path, collect_example_path: &Path) -> Result<ProcessingResult<()>, Box<dyn Error>> {
        // build the test command
        let mut test_cmd = Exec::cmd("npm")
            .arg("run")
            .arg("test")
            .stdin(NullFile)
            .stdout(Redirection::Pipe) // for determining if output
            .cwd(project_path)
            .env("DYN_EXTRACTOR_OUTPUT_PATH", collect_example_path)
            .env("DYN_EXTRACTOR_REPORT_STACKTRACE", self.collect_stack_traces.to_string());

        // set node args, including monkey path
        test_cmd = {
            // if args are not specified, use the default ones
            let mut custom_args = self.custom_node_args.as_ref().map(|args| args.clone()).unwrap_or_default();
            // ensure that monkeypatch is set up
            configure_monkey_patch_env(&self.js_monkeypatch_path, &mut custom_args);
            custom_args.modify_command(test_cmd)
        };

        // configure custom home
        info!("{}: configuring fake home...", package_spec.name());
        test_cmd = self.configure_home(test_cmd)?;
        info!("{}: fake home configured", package_spec.name());

        let cmd = test_cmd.to_cmdline_lossy();

        info!("running test suite by executing [{}]", &cmd);

        let mut test_popen_handle = test_cmd
            .popen()?;

        // read a chunk big enough such that, if there was just an "Error: no test specified"
        let mut chunk = [0u8; 2048];
        test_popen_handle.stdout.as_ref().unwrap().read(&mut chunk)?;

        trace!("read chunk: {:?}", std::str::from_utf8(&chunk).unwrap());

        let test_result = test_popen_handle
            .wait_timeout(self.test_timeout)?;


        // if test suite finished okay, then there's nothing to do
        if test_result.is_some_and(|status| status.success()) {
            return Ok(ProcessingResult::Okay(()))
        }

        // otherwise, we need to figure out an error case
        let result = if test_result.is_some() {
            let extractor_err = match test_result.unwrap() {
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

            if check_has_no_test_suite(&chunk) {
                // if there was no test suite, there was nothing to do, yet it still failed
                ProcessingResult::NoTestSuite
            } else {
                // otherwise, some kind of error really did happen
                ProcessingResult::TestFailed(extractor_err)
            }
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

fn check_has_no_test_suite(chunk: &[u8]) -> bool {
    let finder = regex::bytes::Regex::new(r"Error: no test specified").unwrap();
    finder.is_match(chunk)
}
