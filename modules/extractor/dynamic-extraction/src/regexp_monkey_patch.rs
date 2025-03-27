use std::path::Path;
use crate::custom_node_args::CustomNodeArgs;

/// configures NODE_OPTIONS environment variable to load the JavaScript regexp monekypatching code
/// 
/// By magic, we can make it so that we modify the entire node vm to log regex results. However,
/// we need to do extra work to filter out invalid results.
pub fn configure_monkey_patch_env(monkeypatch_path: &Path, cmd: &mut CustomNodeArgs) {
    let abs_path = monkeypatch_path.canonicalize().unwrap();
    cmd.add_arg("-r", abs_path.to_string_lossy().as_ref());
}