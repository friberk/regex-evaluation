use std::collections::{HashMap};
use std::error::Error;
use log::{error, info};
use db::db_client::{RegexDBClient, RegexDBOperator};
use shared::package_spec::PackageSpec;
use shared::processing_result::{ProcessingResult, ProcessingResultSimple};
use crate::extraction_results::{ExtractionResults, save_extraction_results};
use crate::report::ProcessingReport;

/// takes results from executing extractor and saves into the given database client. Also, returns
/// a report containing info about each project
pub fn save_execution_results(
    associated_packages: HashMap<PackageSpec, Vec<PackageSpec>>,
    mut execution_records: HashMap<PackageSpec, ProcessingResult<ExtractionResults>>,
    db_client: &mut RegexDBClient,
) -> Result<ProcessingReport, Box<dyn Error + 'static>> {
    
    let mut report = ProcessingReport::default();

    info!("Beginning to process execution results...");

    let total = execution_records.len();
    let mut progress_threshold = 10;
    for (index, (parent_package, dependent_packages)) in associated_packages.into_iter().enumerate() {
        // insert the package spec
        let (_, result) = execution_records.remove_entry(&parent_package).expect("parent should be key of execution records");
        save_package_execution(db_client, &mut report, parent_package, dependent_packages, result)?;

        if index * 100 / total >= progress_threshold {
            info!("Currently at {}%", index * 100 / total);
            progress_threshold = progress_threshold + 10;
        }
    }
    
    Ok(report)
}

/// save an individual package execution result in a transaction, i.e., the entire package is
/// transactionally/atomically saved
pub fn save_package_execution(
    db_client: &mut RegexDBClient,
    report: &mut ProcessingReport,
    parent_package: PackageSpec,
    dependent_packages: Vec<PackageSpec>,
    result: ProcessingResult<ExtractionResults>,
) -> Result<(), Box<dyn Error + 'static>> {
    
    let txn = db_client.transaction()?;
    let operator = RegexDBOperator::wrap(&txn);
    
    let parent_id = match operator.insert_package_spec(&parent_package) {
        Ok(id) => id,
        Err(err) => {
            error!("error encountered while saving package spec {}: {}", parent_package.name(), err);
            return Err(err.into());
        }
    };

    for dependent in dependent_packages {
        match operator.insert_dependent_package(parent_id, &dependent) {
            Ok(_) => {}
            Err(err) => {
                error!("error encountered while saving dependent package spec {} (child of {}): {}", parent_package.name(), parent_package.name(), err);
                return Err(err.into());
            }
        }
    }

    match result {
        ProcessingResult::Partial { results, error } => {
            let inner: ProcessingResultSimple = (*error).into();
            let simple_result = ProcessingResultSimple::Partial(inner.into());
            operator.insert_processing_report(parent_id, &simple_result)?;
            report.push_result_simple(parent_package, simple_result);
            save_extraction_results(&operator, parent_id, &results)?
        }
        ProcessingResult::Okay(results) => {
            let result = ProcessingResultSimple::Okay;
            operator.insert_processing_report(parent_id, &result)?;
            report.push_result_simple(parent_package, result);
            save_extraction_results(&operator, parent_id, &results)?
        }
        result => {
            let simple_result = ProcessingResultSimple::from(result);
            operator.insert_processing_report(parent_id, &simple_result)?;
            report.push_result_simple(parent_package, simple_result);
        }
    }

    // commit transaction
    txn.commit()?;
    
    Ok(())
}
