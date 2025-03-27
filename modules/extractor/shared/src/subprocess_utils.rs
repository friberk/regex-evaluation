use std::fmt::Display;
use log::{error, info};
use subprocess::Popen;

// TODO: make logging configurable
/// kill and reap a timed-out process
pub fn kill_and_reap_timed_process<NameT: Display>(handle: &mut Popen, process_name: NameT) {
    match handle.kill() {
        Ok(_) => {
            info!("successfully killed {}. reaping process...", process_name);
            handle.wait().expect("Waiting on a killed process should not fail"); // wait on it
            info!("{} successfully reaped", process_name);
        }
        Err(err) => {
            error!("failed to kill {}: {}, panicking", process_name, err);
            panic!("failed to kill {}", process_name);
        }
    }
}
