use std::collections::HashSet;
use std::error::Error;
use postgres::{Client, Config, NoTls};
use postgres::fallible_iterator::FallibleIterator;
use postgres::types::BorrowToSql;
use shared::package_spec::{PackageSpec, SourceLanguage};

pub struct DbConnectionInfo {
    db_name: String,
    host: String,
    port: u16,
    username: String,
    password: String,
}

impl DbConnectionInfo {
    pub fn new<StrT: Into<String>>(db_name: StrT, host: StrT, port: u16, username: StrT, password: StrT) -> Self {
        Self {
            db_name: db_name.into(),
            host: host.into(),
            port,
            username: username.into(),
            password: password.into()
        }
    }
}

impl Into<Config> for DbConnectionInfo {
    fn into(self) -> Config {
        Client::configure()
            .host(&self.host)
            .port(self.port)
            .dbname(&self.db_name)
            .user(&self.username)
            .password(self.password)
            .to_owned()
    }
}

#[derive(Clone, Copy, Eq, PartialEq, Hash)]
pub enum Ecosystem {
    Maven,
    Npm,
    PyPI
}

impl Ecosystem {
    pub fn to_query_str(&self) -> &str {
        match self {
            Ecosystem::Maven => "maven",
            Ecosystem::Npm => "npm",
            Ecosystem::PyPI => "pypi"
        }
    }
}

impl From<SourceLanguage> for Ecosystem {
    fn from(value: SourceLanguage) -> Self {
        match value {
            SourceLanguage::JAVASCRIPT => Ecosystem::Npm,
            SourceLanguage::JAVA => Ecosystem::Maven,
            SourceLanguage::PYTHON => Ecosystem::PyPI
        }
    }
}

pub struct EcosystemDumpParams {
    /// minimum number of downloads the package needs
    pkg_downloads: i64,
    /// which ecosystems to pull from
    ecosystems: HashSet<Ecosystem>
}

impl EcosystemDumpParams {
    pub fn new(pkg_downloads: i64, ecosystems: HashSet<Ecosystem>) -> Self {
        Self { pkg_downloads, ecosystems }
    }
}

/// pull an ecosystem dump from the specified database location
pub fn pull_ecosystem_dump(
    db_connection_info: DbConnectionInfo,
    params: EcosystemDumpParams,
) -> Result<Vec<PackageSpec>, Box<dyn Error>> {
    
    let config: Config = db_connection_info.into();
    let mut postgres_client = config
        .connect(NoTls)?;
    
    let query_str = include_str!("./sql/pull_ecosystems_query.sql");

    let ecosystem_packages_query = postgres_client.prepare(query_str)?;
    let mut all_packages = Vec::<PackageSpec>::new();
    
    for ecosystem in params.ecosystems {
        let query_results = postgres_client.query_raw(
            &ecosystem_packages_query,
            [
                &params.pkg_downloads, // $1
                ecosystem.to_query_str().borrow_to_sql(), // $2
            ]
        )?;

        let packages = query_results
            .map(|row| {
                let name: String = row.get("name");
                let ecosystem: String = row.get("ecosystem");
                let license: Option<String> = row.get("normalized_licenses");
                let repository_url: String = row.get("repository_url");
                let downloads: i64 = row.get("downloads");

                let source_language = match ecosystem.as_str() {
                    "pypi" => SourceLanguage::PYTHON,
                    "npm" => SourceLanguage::JAVASCRIPT,
                    "maven" => SourceLanguage::JAVA,
                    other => panic!("unsupported ecosystem encountered: {}", other)
                };

                let new_spec = PackageSpec::new(
                    name,
                    repository_url,
                    license.unwrap_or("UNKNOWN".to_string()),
                    source_language,
                    downloads as usize
                );
                
                Ok(new_spec)
            })
            .collect::<Vec<_>>()?;
        
        all_packages.extend(packages);
    }
    
    Ok(all_packages)
}
