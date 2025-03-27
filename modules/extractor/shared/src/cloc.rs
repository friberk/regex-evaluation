use std::error::Error;
use std::fmt::{Display, Formatter};
use std::io::{BufReader, ErrorKind, Read};
use std::path::Path;
use std::time::Duration;
use log::{error, info};

use serde::{Deserialize, Deserializer, Serialize};
use serde::de::{MapAccess, Visitor};
use serde_json::error::Category;
use serde_json::Value;
use subprocess::{Exec, NullFile, PopenError, Redirection};
use crate::package_spec::SourceLanguage;
use crate::subprocess_utils::kill_and_reap_timed_process;

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct ClocLanguageOutput {
    #[serde(rename(deserialize = "nFiles"))]
    files: u32,
    blank: u32,
    comment: u32,
    code: u32,
}

impl ClocLanguageOutput {
    pub fn files(&self) -> u32 {
        self.files
    }
    pub fn blank(&self) -> u32 {
        self.blank
    }
    pub fn comment(&self) -> u32 {
        self.comment
    }
    pub fn code(&self) -> u32 {
        self.code
    }
}

/// Wraps functionality of cloc command
pub struct ClocHarness;

#[derive(Debug)]
pub enum ClocError {
    NotFound,
    IoError(std::io::Error),
    LogicErr(String),
    TimedOut,
    LanguageNotFound,
}

impl Display for ClocError {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        match self {
            ClocError::NotFound => write!(f, "Error while creating cloc harness: cloc executable not found"),
            ClocError::IoError(io_err) => write!(f, "IO Error while finding cloc: {}", io_err),
            ClocError::LogicErr(msg) => write!(f, "logic error while testing cloc: {}", msg),
            ClocError::LanguageNotFound => write!(f, "The queried language was not found in this project"),
            ClocError::TimedOut => write!(f, "cloc timed out on exceptionally large project"),
        }
    }
}

impl Error for ClocError {}

impl ClocHarness {
    pub fn new_from_env() -> Result<Self, ClocError> {
        // determine if there is a cloc binary in the path
        let cloc_version_result = Exec::cmd("cloc")
            .arg("--version")
            .join();

        match cloc_version_result {
            Ok(_) => {
                Ok(Self)
            }
            Err(err) => match err {
                PopenError::IoError(io_err) => match io_err.kind() {
                    ErrorKind::NotFound | ErrorKind::PermissionDenied => {
                        // this command is not in the path
                        Err(ClocError::NotFound)
                    }
                    _ => Err(ClocError::IoError(io_err))
                },
                PopenError::LogicError(msg) => {
                    Err(ClocError::LogicErr(String::from(msg)))
                }
                _ => unreachable!("huh")
            }
        }
    }

    /// Determine how many lines of code are in a directory
    pub fn evaluate_directory(&self, path: &Path, source_language: &SourceLanguage) -> Result<ClocLanguageOutput, ClocError> {
        let lang_include_list = Self::source_lang_to_lang_accept_list(source_language).join(",");
        let cloc_cmd_handle = Exec::cmd("cloc")
            .arg("--include-lang")
            .arg(lang_include_list)
            .arg("--json")
            .arg(path)
            .stdout(Redirection::Pipe)
            .stdin(NullFile);

        info!("running cloc cmd [{}]", cloc_cmd_handle.to_cmdline_lossy());

        let mut cloc_cmd_result = cloc_cmd_handle
            .popen()
            .expect("Once we know cloc exists, executing should not fail...");

        let exit_status = cloc_cmd_result
            .wait_timeout(Duration::from_secs(60 * 3))
            .expect("Waiting should not error");

        match exit_status {
            None => {
                // cloc timed out...
                kill_and_reap_timed_process(&mut cloc_cmd_result, "cloc");
                return Err(ClocError::TimedOut);
            }
            Some(status) => {
                if !status.success() {
                    panic!("Running cloc should never exit with a failure status");
                }
            }
        };

        let output = cloc_cmd_result.stdout.as_ref().expect("Stdout was set, so it should exist");
        let mut output_reader = BufReader::new(output);
        let mut output_string = String::default();
        output_reader.read_to_string(&mut output_string).expect("Reading output should not fail");

        // if there's nothing here, then the language we provided isn't found, so we should not even
        // process this pacakge
        if output_string.trim().is_empty() {
            return Err(ClocError::LanguageNotFound)
        }

        let loc_info = match deserialize_cloc_output(output_string) {
            Ok(info) => info,
            Err(de_err) => match de_err.classify() {
                Category::Data => {
                    error!("data error while processing cloc output: {}", de_err);
                    if let Some(cause) = de_err.source() {
                        error!("cause: {}", cause);
                    }
                    return Err(ClocError::LanguageNotFound);
                }
                _ => {
                    panic!("error while parsing cloc output: {}", de_err);
                }
            }
        };
        
        Ok(loc_info)
    }

    fn source_lang_to_lang_accept_list(source_language: &SourceLanguage) -> &'static [&'static str] {
        match source_language {
            SourceLanguage::JAVASCRIPT => {
                &["JavaScript", "TypeScript"]
            }
            SourceLanguage::JAVA => {
                &["Java"]
            }
            SourceLanguage::PYTHON => {
                &["Python"]
            }
        }
    }
}

struct ClocOutputVisitor;

impl<'de> Visitor<'de> for ClocOutputVisitor {
    type Value = ClocLanguageOutput;

    fn expecting(&self, formatter: &mut Formatter) -> std::fmt::Result {
        formatter.write_str("a valid cloc output")
    }

    fn visit_map<A>(self, mut map: A) -> Result<Self::Value, A::Error> where A: MapAccess<'de> {

        while let Some((next_key, next_value)) = map.next_entry::<String, Value>()? {
            if next_key != "SUM" {
                continue
            }

            // we found the summary chunk
            let output = ClocLanguageOutput::deserialize(next_value);
            return output
                .map_err(|err| serde::de::Error::custom(err))
        }

        return Err(serde::de::Error::missing_field("output didn't have summary field"))
    }
}

fn deserialize_cloc_output<StrT: AsRef<str>>(str_input: StrT) -> serde_json::error::Result<ClocLanguageOutput> {
    let mut deserializer = serde_json::de::Deserializer::from_str(str_input.as_ref());
    deserializer.deserialize_map(ClocOutputVisitor)
}

#[cfg(test)]
mod tests {
    use serde::Deserializer;
    use crate::cloc::ClocOutputVisitor;

    #[test]
    fn deserialize_properly() {
        let input = r#"{"header" : {
  "cloc_url"           : "github.com/AlDanial/cloc",
  "cloc_version"       : "2.00",
  "elapsed_seconds"    : 1.63085889816284,
  "n_files"            : 191,
  "n_lines"            : 654496,
  "files_per_second"   : 117.116201907572,
  "lines_per_second"   : 401319.820333499},
"JavaScript" :{
  "nFiles": 11,
  "blank": 684,
  "comment": 16432,
  "code": 526378},
"TypeScript" :{
  "nFiles": 180,
  "blank": 4660,
  "comment": 59000,
  "code": 47342},
"SUM": {
  "blank": 5344,
  "comment": 75432,
  "code": 573720,
  "nFiles": 191} }
"#;

        let mut deserializer = serde_json::de::Deserializer::from_str(input);
        let output = deserializer.deserialize_map(ClocOutputVisitor).expect("Deserialization should succeed");
        assert_eq!(output.files, 191);
        assert_eq!(output.code, 573720);
        assert_eq!(output.comment, 75432);
        assert_eq!(output.blank, 5344);
    }
}
