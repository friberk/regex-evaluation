use std::error::Error;
use std::io::{Read, Write};
use std::net::TcpStream;
use std::os::unix::net::UnixStream;
use std::path::Path;
use std::time::Duration;
use log::trace;
use shared::regex_entity::ParsedRegexEntity;

enum CommunicationMethod {
    Unix(UnixStream),
    Tcp(TcpStream)
}

impl Write for CommunicationMethod {
    fn write(&mut self, buf: &[u8]) -> std::io::Result<usize> {
        match self {
            CommunicationMethod::Unix(stream) => stream.write(buf),
            CommunicationMethod::Tcp(stream) => stream.write(buf),
        }
    }

    fn flush(&mut self) -> std::io::Result<()> {
        match self {
            CommunicationMethod::Unix(stream) => stream.flush(),
            CommunicationMethod::Tcp(stream) => stream.flush(),
        }
    }
}

impl Read for CommunicationMethod {
    fn read(&mut self, buf: &mut [u8]) -> std::io::Result<usize> {
        match self {
            CommunicationMethod::Unix(stream) => stream.read(buf),
            CommunicationMethod::Tcp(stream) => stream.read(buf),
        }
    }
}

/// A client connection for interacting with a static extractor server. Using this struct, you can
/// send paths to be statically extracted and receive results.
pub struct ExtractorConnection {
    /// communication
    stream: CommunicationMethod
}

impl ExtractorConnection {
    pub(crate) fn new_unix(stream: UnixStream) -> Self {
        Self {
            stream: CommunicationMethod::Unix(stream)
        }
    }

    pub(crate) fn new_tcp(stream: TcpStream) -> Self {
        Self {
            stream: CommunicationMethod::Tcp(stream)
        }
    }
    
    pub fn set_read_timeout(&mut self, duration: Duration) -> std::io::Result<()> {
        match &mut self.stream {
            CommunicationMethod::Unix(unix) => {
                unix.set_read_timeout(Some(duration))
            }
            CommunicationMethod::Tcp(tcp) => {
                tcp.set_read_timeout(Some(duration))
            }
        }
    }

    /// submit a path to be statically extracted
    pub fn send_path(&mut self, path: &Path) -> std::io::Result<()> {
        self.stream.write_all(path.as_os_str().as_encoded_bytes())?;
        self.send_newline()
    }

    /// once there are no more paths to send, tell the static extractor we are done. NOTE: this must
    /// be called or no results will be read. Also, make sure to call this after you are all done.
    pub fn send_done(&mut self) -> std::io::Result<()> {
        self.send_newline()
    }

    #[inline]
    fn send_newline(&mut self) -> std::io::Result<()> {
        self.stream.write_all(&['\n' as u8])
    }
    
    /// collect all results from the static extractor.
    pub fn recv_response(&mut self) -> Result<Vec<ParsedRegexEntity>, Box<dyn Error>> {
        // read all content
        let mut all_content: Vec<u8> = Vec::new();
        self.stream.read_to_end(&mut all_content)?;
        trace!("response payload:\n{}", String::from_utf8(all_content.clone())?);
        
        // split each at newline
        let content_string = String::from_utf8(all_content)?;
        let mut all_entities: Vec<ParsedRegexEntity> = Vec::new();
        for line in content_string.split("\r\n").map(|line| line.trim()).filter(|line| !line.is_empty()) {
            let vector_entities = serde_json::from_str::<Vec<ParsedRegexEntity>>(line)?;
            all_entities.extend(vector_entities);
        }
        
        Ok(all_entities)
    }
}
