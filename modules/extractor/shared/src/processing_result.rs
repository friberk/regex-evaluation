use std::fmt::{Debug, Display, Formatter};
use serde::{Serialize, Serializer};
use serde::ser::SerializeMap;
use crate::error::ExtractorError;

/// Represents the many results that can be produced while extracting a package.
#[derive(Debug)]
pub enum ProcessingResult<T>
    where T: Clone + Debug + Serialize
{
    /// cloning failed
    CloneFailed(ExtractorError),
    /// some error occurred while static extractor was working
    StaticExtractionError,
    /// used to convey if the dynamic extractor build tool is not supported by the project it is
    /// trying to process
    UnsupportedBuildTool,
    /// The language we're interested in processing cannot be found in this directory, so we must
    /// skip it
    LanguageNotFound,
    /// running install failed
    InstallFailed(ExtractorError),
    /// running npm install timed out
    InstallTimeout,
    /// Some error occurred while trying to execute the test suite
    TestFailed(ExtractorError),
    /// running the test suite timed out
    TestTimeout,
    /// general purpose result to show that an error occurred during dynamic extractor
    DynamicExtractorFailed,
    /// The provided package writes the standard message "Error: no test specified", which indicates
    /// that the maintainers have never setup a test suite to be run with npm
    NoTestSuite,
    /// this code means that we had some sort of issue happen, but we still managed to get some
    /// results
    Partial {
        results: T,
        error: Box<Self>,
    },
    /// we completed without any errors
    Okay(T)
}

impl<T> ProcessingResult<T>
    where T: Clone + Debug + Serialize
{
    pub fn change_type<U>(self) -> ProcessingResult<U>
        where U: Clone + Debug + Serialize
    {
        match self {
            ProcessingResult::CloneFailed(err) => ProcessingResult::CloneFailed(err),
            ProcessingResult::StaticExtractionError => ProcessingResult::StaticExtractionError,
            ProcessingResult::UnsupportedBuildTool => ProcessingResult::UnsupportedBuildTool,
            ProcessingResult::LanguageNotFound => ProcessingResult::LanguageNotFound,
            ProcessingResult::InstallFailed(err) => ProcessingResult::InstallFailed(err),
            ProcessingResult::InstallTimeout => ProcessingResult::InstallTimeout,
            ProcessingResult::TestFailed(err) => ProcessingResult::TestFailed(err),
            ProcessingResult::TestTimeout => ProcessingResult::TestTimeout,
            ProcessingResult::DynamicExtractorFailed => ProcessingResult::DynamicExtractorFailed,
            ProcessingResult::NoTestSuite => ProcessingResult::NoTestSuite,
            _ => panic!("This can only be called on error types")
        }
    }

    pub fn is_okay(&self) -> bool {
        match self {
            Self::Okay(_) => true,
            _ => false,
        }
    }
}

impl<T> Display for ProcessingResult<T>
    where T: Clone + Debug + Serialize
{
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        match self {
            ProcessingResult::CloneFailed(err) => write!(f, "Failed while cloning: {}", err),
            ProcessingResult::UnsupportedBuildTool => write!(f, "Build tool not supported by project"),
            ProcessingResult::LanguageNotFound => write!(f, "The language we are extracting from was not found in this project"),
            ProcessingResult::InstallFailed(err) => write!(f, "Failed while installing package dependencies: {}", err),
            ProcessingResult::InstallTimeout => write!(f, "installing package dependencies timed out"),
            ProcessingResult::TestFailed(err) => write!(f, "Failed while running test suite: {}", err),
            ProcessingResult::TestTimeout => write!(f, "test suite timed out"),
            ProcessingResult::DynamicExtractorFailed => write!(f, "Error during dynamic extractor"),
            /*
            ProcessingResult::Partial { results, error } => {
                writeln!(f, "Got error: {}", error)?;
                write!(f, "HOWEVER, still got results:\n{}", results)
            }
            ProcessingResult::Okay(results) => write!(f, "Got results:\n{}", results),
             */
            ProcessingResult::StaticExtractionError => write!(f, "Error during static extractor"),
            ProcessingResult::NoTestSuite => write!(f, "No Test Suite Specified"),
            ProcessingResult::Partial { error, .. } => write!(f, "Encountered error, but got results: {}", error),
            ProcessingResult::Okay(_) => write!(f, "Successfully processed")
        }
    }
}

/// A flat representation of processing result. This is used for thread safety.
#[derive(Debug)]
pub enum ProcessingResultSimple {
    CloneFailed(ExtractorError),
    /// some error occurred while running the static extractor
    StaticExtractionError,
    /// build tool isn't supported
    UnsupportedBuildTool,
    /// The language we are interested in is not found
    LanguageNotFound,
    /// running install failed
    InstallFailed(ExtractorError),
    /// running npm install timed out
    InstallTimeout,
    /// Some error occurred while trying to execute the test suite
    TestFailed(ExtractorError),
    /// running the test suite timed out
    TestTimeout,
    /// Some error occurred during dynamic extractor
    DynamicExtractionError,
    /// The provided package writes the standard message "Error: no test specified", which indicates
    /// that the maintainers have never setup a test suite to be run with npm
    NoTestSuite,
    /// this code means that we had some sort of issue happen, but we still managed to get some
    /// results
    Partial(Box<Self>),
    /// we completed without any errors
    Okay
}

impl ProcessingResultSimple {
    pub fn simple_name(&self) -> &'static str {
        match self {
            ProcessingResultSimple::CloneFailed(_) => "CLONE FAILED",
            ProcessingResultSimple::StaticExtractionError => "STATIC EXTRACTOR FAILED",
            ProcessingResultSimple::UnsupportedBuildTool => "BUILD TOOL NOT SUPPORTED",
            ProcessingResultSimple::LanguageNotFound => "LANGUAGE NOT FOUND",
            ProcessingResultSimple::InstallFailed(_) => "INSTALL FAILED",
            ProcessingResultSimple::InstallTimeout => "INSTALL TIMEOUT",
            ProcessingResultSimple::TestFailed(_) => "TEST FAILED",
            ProcessingResultSimple::TestTimeout => "TEST TIMEOUT",
            ProcessingResultSimple::DynamicExtractionError => "DYNAMIC EXTRACTOR FAILED",
            ProcessingResultSimple::Partial(_) => "PARTIAL",
            ProcessingResultSimple::Okay => "OKAY",
            ProcessingResultSimple::NoTestSuite => "NO TEST SUITE",
        }
    }
    
    pub fn cause_str(&self) -> String {
        match self {
            ProcessingResultSimple::CloneFailed(err) => err.to_string(),
            ProcessingResultSimple::StaticExtractionError => String::from("Encountered an error while communicating with the static extractor"),
            ProcessingResultSimple::UnsupportedBuildTool => String::from("Build tool not supported by project"),
            ProcessingResultSimple::LanguageNotFound => String::from("Language we are extracting was not found in this project"),
            ProcessingResultSimple::InstallFailed(err) => err.to_string(),
            ProcessingResultSimple::InstallTimeout => String::from("Installation took too long"),
            ProcessingResultSimple::TestFailed(err) => err.to_string(),
            ProcessingResultSimple::TestTimeout => String::from("testing"),
            ProcessingResultSimple::DynamicExtractionError => String::from("Encountered an error while performing dynamic extraction"),
            ProcessingResultSimple::Partial(inner) => inner.cause_str(),
            ProcessingResultSimple::Okay => String::from("success"),
            ProcessingResultSimple::NoTestSuite => String::from("Maintainers did not specify test suite, default 'no test suite' message found"),
        }
    }
    
    /// produce status text that is used for project reporting in the database
    pub fn db_status(&self) -> String {
        match self {
            ProcessingResultSimple::Partial(inner) => {
                format!("PARTIAL - {}", inner.db_status())
            },
            other => String::from(other.simple_name())
        }
    }
}

impl<T> From<ProcessingResult<T>> for ProcessingResultSimple
    where T: Clone + Debug + Serialize
{
    fn from(value: ProcessingResult<T>) -> Self {
        match value {
            ProcessingResult::CloneFailed(err) => ProcessingResultSimple::CloneFailed(err),
            ProcessingResult::StaticExtractionError => ProcessingResultSimple::StaticExtractionError,
            ProcessingResult::UnsupportedBuildTool => ProcessingResultSimple::UnsupportedBuildTool,
            ProcessingResult::LanguageNotFound => ProcessingResultSimple::LanguageNotFound,
            ProcessingResult::InstallFailed(err) => ProcessingResultSimple::InstallFailed(err),
            ProcessingResult::InstallTimeout => ProcessingResultSimple::InstallTimeout,
            ProcessingResult::TestFailed(err) => ProcessingResultSimple::TestFailed(err),
            ProcessingResult::TestTimeout => ProcessingResultSimple::TestTimeout,
            ProcessingResult::Partial { error, .. } => {
                let simple_error: Self = (*error).into();
                ProcessingResultSimple::Partial(simple_error.into())
            },
            ProcessingResult::Okay(_) => ProcessingResultSimple::Okay,
            ProcessingResult::DynamicExtractorFailed => ProcessingResultSimple::DynamicExtractionError,
            ProcessingResult::NoTestSuite => ProcessingResultSimple::NoTestSuite,
        }
    }
}

impl Serialize for ProcessingResultSimple {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error> where S: Serializer {
        let mut result_map = serializer.serialize_map(Some(2))?;
        result_map.serialize_entry("type", self.simple_name())?;
        result_map.serialize_entry("cause", &self.cause_str())?;
        if let ProcessingResultSimple::Partial(inner) = self {
            result_map.serialize_entry("inner", inner)?;
        }
        
        result_map.end()
    }
}
