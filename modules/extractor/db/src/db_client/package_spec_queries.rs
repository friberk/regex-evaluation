use rusqlite::{Connection, Error, named_params};
use shared::package_spec::{PackageSpec, SourceLanguage};
use crate::db_client::ExistingRowError;

pub fn find_existing_project_spec(connection: &Connection, repo: &str) -> Result<usize, ExistingRowError> {
    let mut stmt = connection.prepare_cached("SELECT id FROM project_spec WHERE repo = :repo")?;
    let mut rows = stmt.query(named_params! {
            ":repo": repo
        })?;

    let first_row = rows.next()?;
    let Some(first_row) = first_row else {
        return Err(ExistingRowError::NotFound)
    };

    let id: usize = first_row.get(0)?;

    Ok(id)
}

pub fn insert_project_spec(connection: &Connection, spec: &PackageSpec) -> Result<usize, Error> {
    let lang_rep = match spec.language() {
        SourceLanguage::JAVASCRIPT => "JAVASCRIPT",
        SourceLanguage::JAVA => "JAVA",
        SourceLanguage::PYTHON => "PYTHON"
    };
    
    let mut insert_stmt = connection.prepare_cached("INSERT OR IGNORE INTO project_spec (name, repo, license, language, downloads) VALUES (:name, :repo, :license, :language, :downloads)")?;
    
    insert_stmt.execute(
        named_params! {
            ":name": spec.name(),
            ":repo": spec.repo(),
            ":license": spec.license(),
            ":language": lang_rep,
            ":downloads": spec.downloads()
        }
    )?;

    match find_existing_project_spec(connection, spec.repo()) {
        Ok(id) => Ok(id),
        Err(err) => match err {
            ExistingRowError::DBError(err) => Err(err),
            ExistingRowError::NotFound => panic!("after inserting a project spec, it should be found")
        }
    }
}
