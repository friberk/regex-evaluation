use std::collections::HashSet;
use std::error::Error;
use std::fmt::{Display, Formatter};
use log::warn;
use regex::{Regex};
use regex_automata::dfa::Automaton;
use regex_automata::{Input, MatchError};
use serde::{Deserialize, Serialize};

/// Describes a unit that can be evaluated.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RegexTestCase {
    /// positive (matching) example strings
    positive: HashSet<String>,
    /// negative (non-matching) example strings
    negative: HashSet<String>,
    /// ground truth regex pattern
    truth: String,
    /// the package spec that originated this test case 
    package_id: usize,
}

#[derive(Debug)]
pub enum TestCaseError {
    InvalidPattern
}

impl Display for TestCaseError {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        write!(f, "{:?}", self)
    }
}

impl Error for TestCaseError {}

impl RegexTestCase {
    pub fn new<StrT: Into<String> + AsRef<str>>(package_id: usize, pattern: StrT, strings: HashSet<String>) -> Result<Self, TestCaseError> {
        let regex = Regex::new(pattern.as_ref())
            .map_err(|_| TestCaseError::InvalidPattern)?;

        let mut positive = HashSet::<String>::new();
        let mut negative = HashSet::<String>::new();

        for string in strings {
            if regex.is_match(&string) {
                positive.insert(string);
            } else {
                negative.insert(string);
            }
        }

        Ok(Self {
            package_id,
            truth: pattern.into(),
            positive,
            negative
        })
    }

    pub fn total_examples(&self) -> usize {
        self.positive.len() + self.negative.len()
    }

    pub fn test_regex(&self, pattern: &str) -> bool {

        let Ok(regex) = Regex::new(pattern) else {
            warn!("failed to compile regex /{}/", pattern);
            return false;
        };

        for positive in &self.positive {
            if !regex.is_match(positive) {
                return false;
            }
        }

        for negative in &self.negative {
            if regex.is_match(negative) {
                return false;
            }
        }

        true
    }
    
    pub fn test_regex_dfa<DfaT: Automaton>(&self, dfa: &DfaT) -> Result<bool, MatchError> {
        for positive in &self.positive {
            let positive_input = Input::new(positive);
            let search_result = dfa.try_search_fwd(&positive_input)?;
            if search_result.is_none() {
                // there was no match, so return false
                return Ok(false);
            }
        }
        
        for negative in &self.negative {
            let negative_input = Input::new(negative);
            let search_result = dfa.try_search_fwd(&negative_input)?;
            if search_result.is_some() {
                // there was no match, so return false
                return Ok(false);
            }
        }
        
        Ok(true)
    }

    pub fn positive(&self) -> &HashSet<String> {
        &self.positive
    }
    pub fn negative(&self) -> &HashSet<String> {
        &self.negative
    }
    pub fn truth(&self) -> &str {
        &self.truth
    }
    pub fn package_id(&self) -> usize {
        self.package_id
    }
}
