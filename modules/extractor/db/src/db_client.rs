mod regex_entity_queries;
mod package_spec_queries;
pub mod test_suites;

use std::ops::{Deref, DerefMut};
use std::path::Path;
use std::pin::Pin;
use std::str::FromStr;
use rusqlite::{Connection, DatabaseName, Error, named_params, Transaction};
use log::{debug};
use shared::cloc::ClocLanguageOutput;
use shared::package_spec::{PackageSpec, SourceLanguage};
use shared::processing_result::ProcessingResultSimple;
use shared::regex_entity::RegexEntity;
use shared::usage::UsageRecord;
use crate::db_client::package_spec_queries::{insert_project_spec};
use crate::db_client::regex_entity_queries::{insert_new_regex_entity, insert_new_regex_entity_raw, set_regex_entity_dynamic_flag, set_regex_entity_static_flag};

pub struct RegexDBClient {
    connection: Connection
}

impl From<Connection> for RegexDBClient {
    fn from(value: Connection) -> Self {
        Self {
            connection: value
        }
    }
}

impl Deref for RegexDBClient {
    type Target = Connection;

    fn deref(&self) -> &Self::Target {
        &self.connection
    }
}

impl DerefMut for RegexDBClient {
    fn deref_mut(&mut self) -> &mut Self::Target {
        &mut self.connection
    }
}

impl RegexDBClient {
    pub fn new<PathT: AsRef<Path>>(path: PathT) -> rusqlite::Result<Self> {
        Connection::open(path.as_ref())
            .map(|connection| Self { connection })
    }

    /// TODO make this take an enum
    pub fn set_synchronous_pragma(&self, mode: &str) -> rusqlite::Result<()> {
        self.connection.pragma_update(Some(DatabaseName::Main), "synchronous", mode)
    }

    /// creates the necessary tables in a SQLite database
    pub fn initialize_regex_database(&self) -> Result<(), Error> {
        let create_tables_query = include_str!("sql/create_tables.sql");
        self.connection.execute_batch(create_tables_query)
            .map(|_| ())
    }

    /// get a new DB operator from this connection
    pub fn operator(&self) -> RegexDBOperator {
        RegexDBOperator::wrap(&self.connection)
    }
}

pub struct RegexDBOperator<'db> {
    connection: &'db Connection
}

impl<'db> RegexDBOperator<'db> {
    pub fn wrap(connection: &'db Connection) -> Self {
        Self {
            connection
        }
    }

    pub fn insert_package_spec(&self, package_spec: &PackageSpec) -> Result<usize, Error> {
        let id = insert_project_spec(self.connection, package_spec)?;
        Ok(id)
    }
    
    pub fn insert_regex_entity(&self, entity: &RegexEntity, containing_package_id: usize) -> Result<(), Error> {

        let created_rows = insert_new_regex_entity(self.connection, entity)?;
        if created_rows == 0 {
            // this means the pattern already exists, ensure that it is set to static because it
            // was statically extracted
            set_regex_entity_static_flag(self.connection, entity.pattern(), true)?;
        }
        
        let modified_row_count = {
            let query_text = include_str!("sql/insert_regex_source_usage.sql");
            let mut insert_stmt = self.connection.prepare_cached(query_text)?;
            insert_stmt.execute(
                named_params! {
                ":line_no": entity.line_no(),
                ":source_file": entity.source_file(),
                ":commit_hash": entity.commit(),
                ":project_id": containing_package_id,
                ":pattern": entity.pattern()
            })?
        };

        // no row was inserted, so we should communicate that??
        if modified_row_count > 0 {
            // commit the transaction on success
            debug!("successfully inserted regex entity: {:?}", entity);
        }
        Ok(())
    }
    
    pub fn insert_regex_subject_usage(&self, usage: &UsageRecord, containing_package_id: usize) -> Result<(), Error> {

        // first, try to create a dynamic regex entity. If this pattern already exists, it'll be
        // ignored as duplicated
        let rows_modified = insert_new_regex_entity_raw(self.connection, usage.pattern(), "", false, true)?;
        if rows_modified == 0 {
            // this entity already exists. Check that it was dynamically extracted
            set_regex_entity_dynamic_flag(self.connection, usage.pattern(), true)?;
        }

        let query_text = include_str!("sql/insert_regex_subject.sql");
        
        // insert the object
        // when this executed, we are guaranteed to have a pattern. It might be dynamic though
        let modified_row_count = {
            let mut insert_stmt = self.connection.prepare_cached(query_text)?;
            insert_stmt.execute(
                named_params! {
                ":pattern": usage.pattern(),
                ":project_id": containing_package_id,
                ":subject": usage.subject(),
                ":matches": false,
                ":func": usage.func_name()
            })?
        };
        
        if modified_row_count > 0 {
            debug!("successfully inserted subject: {:?}", usage);
        }
        
        Ok(())
    }
    
    pub fn insert_processing_report(&self, package_id: usize, status: &ProcessingResultSimple) -> Result<(), Error> {
        
        let status_str = status.db_status();
        
        let mut insert_stmt = self.connection.prepare_cached("INSERT OR IGNORE INTO project_processing_report (project_id, status) VALUES (:project_id, :status)",)?;
        let modified = insert_stmt.execute(
        named_params! {
                ":project_id": package_id,
                ":status": status_str
            }
        )?;
        
        if modified > 0 {
            debug!("successfully inserted processing report")
        }
        
        Ok(())
    }
    
    pub fn insert_dependent_package(&self, parent_package_id: usize, package_spec: &PackageSpec) -> rusqlite::Result<()> {
        let modified = self.connection.execute(
            "INSERT OR IGNORE INTO duplicate_project_specs (name, downloads, parent_project_id) VALUES (:name, :downloads, :parent_project_id)",
            named_params! {
                ":name": package_spec.name(),
                ":downloads": package_spec.downloads(),
                ":parent_project_id": parent_package_id
            }
        )?;

        if modified > 0 {
            debug!("successfully inserted processing report")
        }
        
        Ok(())
    }
    
    pub fn insert_project_loc(&self, project_id: usize, loc_info: &ClocLanguageOutput) -> rusqlite::Result<()> {
        self.connection.execute(
            "INSERT INTO project_loc_info VALUES (:project_id, :files, :blank, :comment, :code)",
            named_params! {
                ":project_id": project_id,
                ":files": loc_info.files(),
                ":blank": loc_info.blank(),
                ":comment": loc_info.comment(),
                ":code": loc_info.code()
            }
        )
            .map(|_| ())
    }
    
    pub fn load_project_spec_repos(&self) -> rusqlite::Result<Vec<(SourceLanguage, String)>> {
        let query = include_str!("sql/load_project_spec_repos.sql");
        let items = self.connection.prepare(query)
            .unwrap()
            .query_map(
            named_params! {},
            |row| {
                let language_str = row.get_ref_unwrap("language").as_str()?;
                let source_language = SourceLanguage::from_str(language_str).expect("Should work");
                let repo = row.get_ref_unwrap("repo").as_str()?;
                
                Ok((source_language, repo.to_string()))
            }
        )?
            .flat_map(|item| item.into_iter())
            .collect::<Vec<_>>();
        
        Ok(items)
    }
}

enum ExistingRowError {
    DBError(Error),
    NotFound
}

impl From<Error> for ExistingRowError {
    fn from(value: Error) -> Self {
        ExistingRowError::DBError(value)
    }
}
