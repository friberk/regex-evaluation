use log::{warn};
use subprocess::{Exec};

/// Clear and remove all environment variables from command, except for path variable
pub(crate) fn clear_env_except_for_path(mut cmd: Exec) -> Exec {
    cmd = cmd.env_clear();
    const PATH_VAR: &'static str = "PATH";
    let system_path = std::env::var(PATH_VAR);
    let Ok(path) = system_path else {
        warn!("error while accessing variable '{}' from env: {}", PATH_VAR, system_path.unwrap_err());
        return cmd;
    };

    cmd.env(PATH_VAR, path)
}
