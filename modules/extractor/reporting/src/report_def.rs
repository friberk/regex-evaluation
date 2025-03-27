use std::collections::HashMap;
use std::error::Error;
use polars::error::PolarsResult;
use polars::prelude::{AnyValue, DataFrame, NamedFrom};
use polars::series::Series;
use rusqlite::Connection;
use serde::{Deserialize, Serialize};
use crate::util::convert_sqlite_value_ref;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReportDefinition {
    /// an optional id for the report
    id: Option<String>,
    /// the name of this query
    pub(crate) name: String,
    /// an optional query to create a temporary table
    tmp_table_query: Option<String>,
    /// the actual SQL query to run to pull report data. Should be a SELECT
    query: String,
    /// ordered list of column names
    columns: Vec<String>,
    /// determines if the columns on this sheet should fit data
    auto_width_columns: Option<bool>,
    /// if this report should be ignored
    ignored: Option<bool>,
}

impl ReportDefinition {
    pub fn pull_report(&self, db: &Connection) -> Result<DataFrame, Box<dyn Error>> {

        // create tmp table if necessary
        self.create_tmp_table(db)?;

        // actually produce the report
        let mut series_map = make_series_map(&self.columns);
        let mut stmt = db.prepare(&self.query)?;
        let mut rows = stmt.query([])?;
        while let Ok(Some(row)) = rows.next() {
            for column in &self.columns {
                let column_value = row.get_ref(column.as_str())?;
                let df_value = convert_sqlite_value_ref(column_value);
                series_map.get_mut(column).unwrap().push(df_value);
            }
        }

        // convert
        let df = series_map_into_df(&self.columns, series_map)?;
        Ok(df)
    }

    fn create_tmp_table(&self, connection: &Connection) -> rusqlite::Result<()> {
        if let Some(table_query) = self.tmp_table_query.as_ref() {
            connection.execute_batch(table_query)?;
        }

        Ok(())
    }

    /// if not specified, defaults to true
    pub fn auto_width_column(&self) -> bool {
        self.auto_width_columns.unwrap_or(true)
    }
    
    /// if this report should be ignored. True means it should be ignored
    pub fn ignored(&self) -> bool {
        self.ignored.unwrap_or(false)
    }
    
    /// an optionally specified id for the report, defaults to the report's name
    pub fn id(&self) -> &str {
        self.id.as_ref().unwrap_or(&self.name)
    }
}

fn make_series_map(series_names: &[String]) -> HashMap<String, Vec<AnyValue>> {
    let mut series = HashMap::<String, Vec<AnyValue>>::new();
    for name in series_names {
        series.insert(name.clone(), Vec::default());
    }

    series
}

fn series_map_into_df(order: &[String], mut raw_data: HashMap<String, Vec<AnyValue>>) -> PolarsResult<DataFrame> {

    let mut columns = Vec::<Series>::new();
    for column_name in order {
        let raw_values = raw_data.remove(column_name).expect("column name must be in map");
        columns.push(Series::new(column_name, raw_values));
    }

    DataFrame::new(columns)
}
