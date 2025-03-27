use std::collections::HashMap;
use std::fmt::Debug;
use serde::{Serialize, Serializer};
use serde::ser::SerializeMap;
use shared::package_spec::PackageSpec;
use shared::processing_result::{ProcessingResult, ProcessingResultSimple};

/// a basic report of what happened to each project. We want to trace the results of parsing each of
/// these projects, so we want to know things like: did it fail to clone? was there an error while
/// running the test suite? etc.
#[derive(Debug, Default)]
pub struct ProcessingReport {
    results: HashMap<String, ProcessingResultSimple>
}

impl ProcessingReport {
    pub fn push_result<T>(&mut self, package_spec: PackageSpec, result: ProcessingResult<T>)
        where T: Clone + Debug + Serialize
    {
        self.push_result_simple(package_spec, result.into());
    }

    pub fn push_result_simple(&mut self, package_spec: PackageSpec, result: ProcessingResultSimple)
    {
        self.results.insert(package_spec.take_repo(), result);
    }
}

impl Serialize for ProcessingReport {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error> where S: Serializer {
        let mut report_map = serializer.serialize_map(Some(self.results.len()))?;
        for (project, simple_result) in &self.results {
            report_map.serialize_entry(project, simple_result)?;
        }
        
        report_map.end()
    }
}
