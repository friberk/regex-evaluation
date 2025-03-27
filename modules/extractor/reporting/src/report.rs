use std::collections::HashMap;
use std::error::Error;
use std::fs::File;
use std::io::BufWriter;
use std::path::Path;
use log::info;
use polars::frame::DataFrame;
use polars::prelude::{CsvWriter, SerWriter};
use rust_xlsxwriter::{ColNum, Format, FormatAlign, RowNum, Workbook, Worksheet};
use serde::{Serialize, Serializer};
use serde::ser::SerializeMap;
use crate::report_def::ReportDefinition;
use crate::util::write_polars_value;

/// Describes a fully combined report order
pub struct CharacteristicsReport {
    /// Named reports
    reports: HashMap<String, (ReportDefinition, DataFrame)>,
    /// How to order each report
    report_order: Vec<String>,
}

impl CharacteristicsReport {
    pub fn new() -> Self {
        Self {
            reports: HashMap::new(),
            report_order: Vec::new(),
        }
    }

    pub fn push_report(&mut self, report_data: DataFrame, def: ReportDefinition) {
        let name = def.name.clone();
        self.reports.insert(name.clone(), (def, report_data));
        self.report_order.push(name);
    }

    pub fn write_to_xlsx(mut self, output_path: &Path) -> Result<(), Box<dyn Error>> {

        let mut wb = Workbook::new();

        for report_name in self.report_order {
            let report_ws = wb.add_worksheet().set_name(&report_name)?;
            let (def, report) = self.reports.remove(&report_name).unwrap();

            write_to_worksheet(report, report_ws, (0, 0))?;

            if def.auto_width_column() {
                report_ws.autofit();
            }
        }

        wb.save(output_path)?;

        Ok(())
    }

    pub fn write_to_csv(self, csv_collect_dir: &Path) -> Result<(), Box<dyn Error>> {
        // make the collect directory if necessary
        if !csv_collect_dir.try_exists()? {
            std::fs::create_dir(csv_collect_dir)?;
        }

        info!("writing csv reports to directory {}", csv_collect_dir.display());

        // write each report to a csv file in the directory
        for (report_name, (def, mut report)) in self.reports {
            let report_file_name = format!("{}.csv", def.id());
            let output_path = csv_collect_dir.join(report_file_name);
            info!("writing {} to {}", report_name, output_path.display());
            let output_file = File::create(output_path)?;
            let output_writer = BufWriter::new(output_file);
            CsvWriter::new(output_writer)
                .include_header(true)
                .finish(&mut report)?;
            info!("successfully wrote {}", report_name);
        }

        Ok(())
    }
}

fn write_to_worksheet(data_frame: DataFrame, worksheet: &mut Worksheet, origin: (RowNum, ColNum)) -> Result<(RowNum, ColNum), Box<dyn Error>> {
    let data = data_frame;
    let (origin_row, origin_col) = origin;

    let mut ending_row = origin_row;
    let mut ending_col = origin_col;
    let header_format = Format::new()
        .set_align(FormatAlign::Center)
        .set_bold();
    for (col_offset, series) in data.iter().enumerate() {
        let write_col = origin_col + (col_offset as u16);
        worksheet.write_with_format(origin_row, write_col, series.name(), &header_format)?;

        for (row_offset, value) in series.iter().enumerate() {
            let write_row = origin_row + 1 + (row_offset as u32); // the +1 skips the header
            write_polars_value(worksheet, write_row, write_col, value)?;
            // the compiler should fix these up :)
            ending_row = write_row;
            ending_col = write_col;
        }
    }

    Ok((ending_row, ending_col))
}

impl Serialize for CharacteristicsReport {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error> where S: Serializer {
        let mut report_map = serializer.serialize_map(Some(self.report_order.len()))?;
        for report_name in &self.report_order {
            let report_data = self.reports.get(report_name).unwrap();
            report_map.serialize_entry(report_name, report_data)?;
        }
        report_map.end()
    }
}
