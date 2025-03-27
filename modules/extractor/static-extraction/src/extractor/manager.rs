use std::error::Error;
use std::fs::File;
use std::io;
use subprocess::{Exec, NullFile, Popen, Redirection};
use shared::package_spec::SourceLanguage;

use std::net::{IpAddr, Ipv4Addr, SocketAddr as IpSocketAddr, TcpStream};
use std::os::unix::net::{SocketAddr as UnixSocketAddr, UnixStream};
use std::path::{Path};
use std::time::Duration;
use log::{debug, error, info};
use shared::error::ExtractorError;
use crate::extractor::connection::ExtractorConnection;
use crate::extractor::extractor_info::{ExtractorInfo, ExtractorServerConnectionInfo};

pub enum ExtractorServerMethod {
    UnixServer(UnixSocketAddr),
    TcpServer(IpSocketAddr)
}

impl TryFrom<ExtractorServerConnectionInfo> for ExtractorServerMethod {
    type Error = Box<dyn Error>;

    fn try_from(value: ExtractorServerConnectionInfo) -> Result<Self, Self::Error> {
        match value {
            ExtractorServerConnectionInfo::Unix(path) => {
                let unix_addr = UnixSocketAddr::from_pathname(path)?;
                Ok(Self::unix(unix_addr))
            }
            ExtractorServerConnectionInfo::Tcp(port) => {
                let ip_addr = IpSocketAddr::new(IpAddr::V4(Ipv4Addr::LOCALHOST), port);
                Ok(Self::tcp(ip_addr))
            }
        }
    }
}

impl ExtractorServerMethod {
    pub fn tcp(addr: IpSocketAddr) -> Self {
        Self::TcpServer(addr)
    }

    pub fn unix(addr: UnixSocketAddr) -> Self {
        Self::UnixServer(addr)
    }
}

/// RAII process manager to manage static extractor server processes. This holds a handle to the
/// running static extractor process, information on how to connect to the process, and other
/// metadata. When this instance falls out of scope, the subprocess is terminated.
pub struct ExtractorManager {
    /// the actual process that we are managing
    extractor_process: Popen,
    /// how to connect to the server
    connection_info: ExtractorServerMethod,
    /// hold onto info about extractor
    extractor_info: ExtractorInfo,
}

impl ExtractorManager {
    pub fn new(extractor_info: ExtractorInfo, show_output: bool, extractor_logs_dir: Option<&Path>) -> Result<Self, Box<dyn Error>> {

        let connection_info = ExtractorServerMethod::try_from(extractor_info.connection_info().clone())?;
        let connection_str: String = extractor_info.connection_info().clone().into();
        
        let extractor_cmd = {
            let mut cmd = if let Some(exec_command) = extractor_info.executing_command() {
                Exec::cmd(exec_command)
                    .arg(extractor_info.extractor_path())
            } else {
                Exec::cmd(extractor_info.extractor_path())
            };
            
            cmd = cmd
                .arg(connection_str.as_str())
                .arg(extractor_info.workers().to_string());
            
            cmd = if let Some(log_dir) = extractor_logs_dir {
                let redirect_file = create_log_file(&extractor_info, log_dir)?;
                cmd
                    .stderr(Redirection::Merge)
                    .stdout(redirect_file)
            } else if !show_output {
                cmd
                    .stderr(Redirection::Merge)
                    .stdout(NullFile)
            } else {
                cmd
            };
            
            cmd
        };
        
        let cmd = extractor_cmd.to_cmdline_lossy();
        debug!("Starting extractor {} with cmd: [{}]", extractor_info.name(), cmd);
        
        let mut subcommand = extractor_cmd
            .popen()?;

        // wait a second and see if the extractor failed
        std::thread::sleep(Duration::from_secs(1));
        if let Some(exit_status) = subcommand.poll() {
            if exit_status.success() {
                panic!("We successfully exited 1 second after starting...")
            }

            return Err(ExtractorError::from(exit_status).with_cmd(cmd).into())
        }

        Ok(Self {
            extractor_process: subcommand,
            connection_info,
            extractor_info,
        })
    }
    
    pub fn can_accept_language(&self,  source_language: &SourceLanguage) -> bool {
        self.extractor_info.source_language() == source_language
    }

    /// Creates a client connection that connects to this static extractor. Clients are cheap, so
    /// make a new one each time
    pub fn create_connection(&self) -> std::io::Result<ExtractorConnection> {
        // create stream
        match &self.connection_info {
            ExtractorServerMethod::UnixServer(unix_addr) => {
                let stream = UnixStream::connect_addr(&unix_addr)?;
                Ok(ExtractorConnection::new_unix(stream))
            }
            ExtractorServerMethod::TcpServer(ip_addr) => {
                let stream = TcpStream::connect(ip_addr)?;
                Ok(ExtractorConnection::new_tcp(stream))
            }
        }
    }

    /// tests if the static extractor is up and running by attempting to connect. If connection is
    /// successful, then clients can connect to the static extractor
    pub fn test_connection(&self) -> Option<std::io::Error> {
        match &self.connection_info {
            ExtractorServerMethod::UnixServer(unix_addr) => {
                UnixStream::connect_addr(&unix_addr).err()
            }
            ExtractorServerMethod::TcpServer(ip_addr) => {
                TcpStream::connect(ip_addr).err()
            }
        }
    }

    pub fn extractor_info(&self) -> &ExtractorInfo {
        &self.extractor_info
    }
}

impl Drop for ExtractorManager {
    fn drop(&mut self) {
        let pid = self.extractor_process.pid();
        let kill_result = self.extractor_process.kill();
        match kill_result {
            Ok(_) => {
                info!("successfully terminated extractor {} (pid {})", self.extractor_info.name(), pid.unwrap_or(0))
            }
            Err(err) => {
                error!("failed to terminate extractor {} (pid {}): {}", self.extractor_info.name(), pid.unwrap_or(0), err)
            }
        }
        
        match &self.connection_info {
            ExtractorServerMethod::UnixServer(path) => {
                if let Some(filename) = path.as_pathname() {
                    match std::fs::remove_file(filename) {
                        Ok(_) => {
                            info!("Successfully removed unix server file {}", filename.to_string_lossy())
                        }
                        Err(err) => {
                            error!("Error while removing socket file: {}", err)
                        }
                    }
                }
            }
            _ => {}
        }
    }
}

fn create_log_file(info: &ExtractorInfo, containing_dir: &Path) -> io::Result<File> {
    // create directory if it doesn't exist
    if !containing_dir.try_exists()? {
        std::fs::create_dir(containing_dir)?;
    }
    
    let file_path = containing_dir.join(format!("extractor-{}.logs", info.name()));
    
    File::create(file_path)
}
