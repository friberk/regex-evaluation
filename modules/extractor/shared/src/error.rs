use std::error::Error;
use std::io;
use subprocess::ExitStatus;

use thiserror::Error;

#[derive(Error, Debug)]
pub enum ExtractorError {
    #[error("Error while starting extractor {name}: {cause}")]
    StartUp {name: String, cause: Box<dyn Error + 'static> },
    #[error("Sub-command [{cmd}] failed with exit code {exit_code}")]
    SubCommandExited {
        exit_code: u32,
        cmd: String,
    },
    #[error("Sub-command [{cmd}] was signaled with signal {exit_signal}")]
    SubCommandSignaled {
        exit_signal: u8,
        cmd: String,
    },
    #[error("Error while executing subcommand: {source}")]
    Subprocess {
        #[from]
        source: subprocess::PopenError,
    },
    #[error("I/O error occurred while {operation}: {source}")]
    IO {
        source: io::Error,
        operation: String,
    },
    #[error("Error: {0}")]
    Other(String)
}

impl ExtractorError {
    pub fn with_cmd<StrT: Into<String>>(self, cmd: StrT) -> Self {
        match self {
            ExtractorError::SubCommandExited { exit_code, .. } => Self::SubCommandExited { exit_code, cmd: cmd.into() },
            ExtractorError::SubCommandSignaled { exit_signal, .. } => Self::SubCommandSignaled { exit_signal, cmd: cmd.into() },
            _ => self
        }
    }
}

impl From<subprocess::ExitStatus> for ExtractorError {
    fn from(value: ExitStatus) -> Self {
        match value {
            ExitStatus::Exited(code) => {
                ExtractorError::SubCommandExited {exit_code: code, cmd: "".to_string() }
            }
            ExitStatus::Signaled(signal) => {
                ExtractorError::SubCommandSignaled {exit_signal: signal, cmd: "".to_string() }
            }
            _ => ExtractorError::Other("Unknown error while executing subprocess".to_string())
        }
    }
}
