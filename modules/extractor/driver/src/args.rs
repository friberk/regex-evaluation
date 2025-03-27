use std::collections::HashSet;
use std::fmt::{Display, Formatter};
use std::path::{Path, PathBuf};
use clap::{Args, Parser, Subcommand, ValueEnum};
use db::db_merge::MergeDatabaseVersion;
#[cfg(feature = "extractor")]
use dynamic_extraction::custom_node_args::CustomNodeArgs;
#[cfg(feature = "extractor")]
use dynamic_extraction::dynamic_extractor_manager::config::JsDynamicExtractorConfig;
use dynamic_extraction::dynamic_extractor_manager::config::MavenDynamicExtractorConfig;
use dynamic_extraction::dynamic_extractor_manager::java::java_home_config::JavaHomes;
#[cfg(feature = "ecosystem-dump")]
use ecosystems_dump::pull_dump::{DbConnectionInfo, Ecosystem, EcosystemDumpParams};
use shared::package_spec::{PackageSpec, SourceLanguage};

#[derive(Debug, Clone, Parser)]
pub struct GlobalArgs {
    /// the command to run
    #[clap(subcommand)]
    pub command: Subcommands
}

#[derive(Debug, Clone, Subcommand)]
pub enum Subcommands {
    /// run the full extraction pipeline (clone -> static extraction -> dynamic extraction (if possible) -> collect)
    #[cfg(feature = "extractor")]
    Extract(ExtractArgs),
    /// run the extraction pipeline on a single package that has already been cloned
    #[cfg(feature = "extractor")]
    ExtractDir(DirExtractArgs),
    /// Merge a set of regex SQLite databases into one
    DbCombine(DbCombineArgs),
    /// Report characteristics about the regex corpus
    #[cfg(feature = "reporting")]
    ReportGen(ReportGenArgs),
    /// Create test suites for the given extraction results
    #[cfg(feature = "evaluation")]
    GenTestSuites(GenTestSuitesArgs),
    /// Generate a database of precompiled regex DFAs from an existing corpus
    #[cfg(feature = "evaluation")]
    #[clap(name = "gen-dfas")]
    GenDFAs(GenDFAsArgs),
    /// perform evaluation experiment
    #[cfg(feature = "evaluation")]
    Evaluate(EvaluationArgs),
    /// Get an ecosystem dump
    #[cfg(feature = "ecosystem-dump")]
    EcosystemDump(EcosystemDumpArgs),
    /// sample packages to process
    SamplePackages(SampleUniqueProjectsArgs),
}

#[derive(Debug, Clone, ValueEnum)]
pub enum SynchronousDbMode {
    Off,
    Normal,
    Full,
    Extra
}

impl SynchronousDbMode {
    pub fn to_db_param(&self) -> &'static str {
        match self {
            SynchronousDbMode::Off => "OFF",
            SynchronousDbMode::Normal => "NORMAL",
            SynchronousDbMode::Full => "FULL",
            SynchronousDbMode::Extra => "EXTRA"
        }
    }
}

impl Display for SynchronousDbMode {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        match self {
            SynchronousDbMode::Off => write!(f, "off"),
            SynchronousDbMode::Normal => write!(f, "normal"),
            SynchronousDbMode::Full => write!(f, "full"),
            SynchronousDbMode::Extra => write!(f, "extra")
        }
    }
}

pub trait ProvidesCommonExtractArgs {
    fn common_args(&self) -> &CommonExtractArgs;
}

#[derive(Debug, Clone, Args)]
pub struct CommonExtractArgs {
    /// path to where the JavaScript RegExp monkey-patching code is 
    #[arg(long, env = "JS_MONKEYPATCH_PATH")]
    js_monkeypatch: PathBuf,
    /// path to where the JDE agent jar file is located
    #[arg(long, env = "JDE_AGENT_PATH")]
    jde_agent: PathBuf,
    /// absolute path to javascript extractor bundle.
    #[arg(long, env = "JS_EXTRACTOR_PATH")]
    js_ext: PathBuf,
    /// absolute path to java extractor fat jar
    #[arg(long, env = "JAVA_EXTRACTOR_PATH")]
    java_ext: PathBuf,
    /// absolute path to python extractor program
    #[arg(long, env = "PYTHON_EXTRACTOR_PATH")]
    py_ext: PathBuf,
    /// If set, displays extractor server output on STDOUT
    #[arg(long, default_value_t = false)]
    extractor_output: bool,
    /// output path to write regex db to
    #[arg(short, long)]
    output: PathBuf,
    /// Where to write the execution processing report (leave empty to skip this step)
    #[arg(short, long)]
    report: Option<PathBuf>,
    /// Optional list of node command line args to pass while running `npm test` to extract regexes.
    /// This string will be split into a map of flags and arguments
    #[arg(long)]
    custom_node_args: Option<String>,
    /// if set to true, collect the stacktrace location of each example
    #[arg(long, default_value_t = false)]
    collect_stack_traces: bool,
    /// if provided, the extractors setup for this extractor process will save logs to this
    /// directory. If the directory does not exist, a new one at this path will be created. This
    /// option will preempt extractor-output, so if both are set, the output will be logged
    #[arg(long)]
    extractor_logs_dir: Option<PathBuf>,
    /// Optionally provide a limit of the number of example strings to save. Any strings found
    /// beyond this limit will be discarded
    #[arg(long)]
    example_string_limit: Option<u32>,
    /// When running extraction, use this option to set the HOME environment variable in the
    /// sub-process. Use this option to keep your home from being polluted
    #[arg(long)]
    fake_home: Option<PathBuf>,
    /// Set the 'synchronous' db pragma
    #[arg(long, default_value_t = SynchronousDbMode::Normal)]
    synchronous_db: SynchronousDbMode,
    /// general timeout for dynamic extractor processes in minutes. Installation, building, and testing each
    /// get this duration before being killed. Format should be something like '5min' or '30s'
    #[arg(long, default_value = "5min")]
    timeout: humantime::Duration,
    /// general installation timeout duration for dynamic installation portion. E.g., how much time
    /// npm gets for `npm install` before calling it timed out. Defaults to --timeout. Format should
    /// be something like '5min' or '30s'
    #[arg(long)]
    install_timeout: Option<humantime::Duration>,
    /// general installation timeout duration for dynamic installation portion. E.g., how much time
    /// npm gets for `npm install` before calling it timed out. Defaults to --timeout. Format should
    /// be something like '5min' or '30s'
    #[arg(long)]
    test_timeout: Option<humantime::Duration>,
    /// optionally specify where the maven local storage should be located.
    #[arg(long)]
    mvn_install_dir: Option<PathBuf>,
    /// if set, and a custom maven installation directory is specified, then the custom install
    /// directory will not be deleted. Default behavior is that the directory will be deleted
    #[arg(long)]
    mvn_install_no_cleanup: bool,
    /// if set, then dynamic extractors will not inherit the environment from the parent process.
    #[arg(long)]
    clean_env: bool,
}

impl CommonExtractArgs {
    pub fn js_extractor_path(&self) -> &PathBuf {
        &self.js_ext
    }
    pub fn java_extractor_path(&self) -> &PathBuf {
        &self.java_ext
    }
    pub fn python_extractor_path(&self) -> &PathBuf {
        &self.py_ext
    }

    pub fn js_monkeypatch_path(&self) -> &PathBuf {
        &self.js_monkeypatch
    }
    
    pub fn show_extractor_output(&self) -> bool {
        self.extractor_output
    }

    pub fn output(&self) -> &PathBuf {
        &self.output
    }
    
    pub fn report(&self) -> Option<&PathBuf> {
        self.report.as_ref()
    }
    
    pub fn custom_node_args(&self) -> Option<CustomNodeArgs> {
        self.custom_node_args.as_ref().and_then(|raw| CustomNodeArgs::parse(raw).ok())
    }
    
    pub fn collect_stack_traces(&self) -> bool {
        self.collect_stack_traces
    }
    
    pub fn extractor_logs_dir(&self) -> &Option<PathBuf> {
        &self.extractor_logs_dir
    }


    pub fn example_string_limit(&self) -> Option<u32> {
        self.example_string_limit
    }

    pub fn fake_home(&self) -> Option<&Path> { self.fake_home.as_ref().map(|pb| pb.as_path()) }

    pub fn js_dynamic_args(&self) -> JsDynamicExtractorConfig {
        JsDynamicExtractorConfig {
            js_monkeypatch_path: self.js_monkeypatch_path(),
            custom_node_args: self.custom_node_args(),
            collect_stack_traces: self.collect_stack_traces,
            example_limit: self.example_string_limit,
            fake_home: self.fake_home(),
            install_duration: *self.install_timeout.clone().unwrap_or(self.timeout.clone().into()),
            test_duration: *self.test_timeout.clone().unwrap_or(self.timeout.clone().into()),
        }
    }
    
    // TODO this is goofy...
    // the reason this is passed as an arg is because args shouldn't have any part in setting it up
    // right now...
    pub fn maven_dynamic_args(&self, java_homes: JavaHomes) -> MavenDynamicExtractorConfig {
        MavenDynamicExtractorConfig {
            jde_agent_path: self.jde_agent.clone(),
            example_limit: self.example_string_limit,
            install_duration: *self.install_timeout.clone().unwrap_or(self.timeout.clone().into()),
            test_duration: *self.test_timeout.clone().unwrap_or(self.timeout.clone().into()),
            fake_home: self.fake_home.clone(),
            java_home_config: java_homes,
            local_install_path: self.mvn_install_dir.clone(),
            clean_env: self.clean_env
        }
    }

    pub fn synchronous_db(&self) -> &SynchronousDbMode {
        &self.synchronous_db
    }
    pub fn mvn_install_dir(&self) -> &Option<PathBuf> {
        &self.mvn_install_dir
    }
    pub fn mvn_install_cleanup(&self) -> bool {
        !self.mvn_install_no_cleanup
    }
}

impl ProvidesCommonExtractArgs for CommonExtractArgs {
    fn common_args(&self) -> &CommonExtractArgs {
        self
    }
}

#[derive(Debug, Clone, ValueEnum)]
pub enum ProcessMode {
    /// each package's processing result is saved as it is processed.
    Incremental,
    /// all packages results are buffered and saved at the end
    Batch
}

impl Display for ProcessMode {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        match self {
            ProcessMode::Incremental => f.write_str("incremental"),
            ProcessMode::Batch => f.write_str("batch"),
        }
    }
}

#[cfg(feature = "extractor")]
#[derive(Debug, Clone, Args)]
pub struct ExtractArgs {
    #[clap(flatten)]
    common: CommonExtractArgs,
    /// if set to false, leave cloned packages to be manually deleted by the user
    #[arg(short, long, default_value_t = false)]
    no_cleanup: bool,
    /// base path to clone packages into. Defaults to TMPDIR
    #[arg(short, long)]
    package_working_dir: Option<PathBuf>,
    /// How package processing should proceed
    #[arg(short, long, default_value_t = ProcessMode::Batch)]
    process_mode: ProcessMode,
    /// A list of files that contain package specs, one on each line
    package_spec_paths: Vec<PathBuf>
}

impl ExtractArgs {
    pub fn cleanup(&self) -> bool {
        !self.no_cleanup
    }

    pub fn package_spec_paths(&self) -> &Vec<PathBuf> {
        &self.package_spec_paths
    }

    pub fn clone_base_path(&self) -> PathBuf {
        self.package_working_dir.clone().unwrap_or(std::env::temp_dir())
    }

    pub fn process_mode(&self) -> &ProcessMode {
        &self.process_mode
    }
}

impl ProvidesCommonExtractArgs for ExtractArgs {
    fn common_args(&self) -> &CommonExtractArgs {
        &self.common
    }
}

#[derive(Debug, Clone, ValueEnum)]
pub enum SourceLanguageArg {
    Python,
    JavaScript,
    Java
}

impl Into<SourceLanguage> for SourceLanguageArg {
    fn into(self) -> SourceLanguage {
        match self {
            SourceLanguageArg::Python => SourceLanguage::PYTHON,
            SourceLanguageArg::JavaScript => SourceLanguage::JAVASCRIPT,
            SourceLanguageArg::Java => SourceLanguage::JAVA
        }
    }
}

#[cfg(feature = "extractor")]
#[derive(Debug, Clone, Args)]
pub struct DirExtractArgs {
    #[clap(flatten)]
    common: CommonExtractArgs,
    /// The source language of this package
    #[arg(short, long)]
    language: SourceLanguageArg,
    /// the directory to extract
    directory: PathBuf
}

impl DirExtractArgs {
    pub fn package_spec(&self) -> Option<PackageSpec> {
        let filename = self.directory.file_name()
            .and_then(|os| os.to_str())
            .map(|filename| filename.to_string())?;

        Some(PackageSpec::local(filename, self.language.clone().into(), self.directory()))
    }

    pub fn directory(&self) -> &PathBuf {
        &self.directory
    }
}

impl ProvidesCommonExtractArgs for DirExtractArgs {
    fn common_args(&self) -> &CommonExtractArgs {
        &self.common
    }
}

#[derive(ValueEnum, Debug, Clone)]
enum VersionArg {
    V1,
    V2
}

impl Into<MergeDatabaseVersion> for VersionArg {
    fn into(self) -> MergeDatabaseVersion {
        match self {
            VersionArg::V1 => MergeDatabaseVersion::V1,
            VersionArg::V2 => MergeDatabaseVersion::V2
        }
    }
}

impl Display for VersionArg {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        match self {
            VersionArg::V1 => f.write_str("v1"),
            VersionArg::V2 => f.write_str("v2"),
        }
    }
}

#[derive(Debug, Clone, Args)]
pub struct DbCombineArgs {
    /// merge all databases into this existing database
    #[arg(short, long)]
    pub existing: Option<PathBuf>,
    /// write merge results into a new databaseEcosystem
    #[arg(short, long)]
    pub new: Option<PathBuf>,
    /// Purge component databases as you go. WARNING: this option will permanently delete all
    /// database components that you merge. While their information will be copied atomically,
    /// think twice before using this feature
    #[arg(short, long)]
    pub purge: bool,
    /// Confirm that you indeed want to purge. If purge is not set, this flag is ignored
    #[arg(short, long)]
    pub confirm: bool,
    /// which merge algorithm version to use
    #[arg(long, default_value_t = VersionArg::V2)]
    version: VersionArg,
    /// the databases to combine. All results will be combined into the first database
    pub database_files: Vec<PathBuf>
}

impl DbCombineArgs {
    pub fn version(&self) -> MergeDatabaseVersion {
        self.version.clone().into()
    }

    pub fn database_files(&self) -> &[PathBuf] {
        &self.database_files
    }
}

#[cfg(feature = "evaluation")]
#[derive(Debug, Clone, Args)]
pub struct GenTestSuitesArgs {
    /// path to write the resulting test suites file to
    #[arg(short, long)]
    pub output: PathBuf,
    /// combined database to pull from
    pub database_file: PathBuf,
}

#[cfg(feature = "evaluation")]
#[derive(Debug, Clone, Args)]
pub struct EvaluationArgs {
    /// optionally provide path to pre-compiled regex DFAs for the given database
    #[arg(short, long)]
    pub dfas_db: PathBuf,
    /// optionally provide pre-computed test suites to use
    #[arg(short, long)]
    pub test_cases_path: Option<PathBuf>,
    /// path to write the resulting test suites file to
    #[arg(short, long)]
    pub output: PathBuf,
    /// combined database to pull from
    pub database_file: PathBuf,
}

#[cfg(feature = "evaluation")]
#[derive(Debug, Clone, Args)]
pub struct GenDFAsArgs {
    /// path of corpus extraction results to read regexes from
    pub corpus_db: PathBuf,
    /// Where to write DFAs to
    pub output_db: PathBuf,
}

/// Describes different choices for output
#[derive(ValueEnum, Debug, Clone)]
pub enum OutputFormat {
    /// NDJSON objects, one json object per line
    NDJSON,
    /// output a JSON list holding all items
    JSON,
}

impl Display for OutputFormat {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        match self {
            OutputFormat::NDJSON => write!(f, "ndjson"),
            OutputFormat::JSON => write!(f, "json")
        }
    }
}

#[cfg(feature = "ecosystem-dump")]
#[derive(Debug, Clone, ValueEnum)]
pub enum EcosystemValue {
    Maven,
    Npm,
    Pypi
}

#[cfg(feature = "ecosystem-dump")]
impl Into<Ecosystem> for EcosystemValue {
    fn into(self) -> Ecosystem {
        match self {
            EcosystemValue::Maven => Ecosystem::Maven,
            EcosystemValue::Npm => Ecosystem::Npm,
            EcosystemValue::Pypi => Ecosystem::PyPI
        }
    }
}

#[cfg(feature = "ecosystem-dump")]
#[derive(Debug, Clone, Args)]
pub struct EcosystemDumpArgs {
    /// the name of the database to connect to
    #[arg(short, long, default_value = "packages_production")]
    pub db_name: String,
    /// the host on which the database is running
    #[arg(short, long, default_value = "localhost")]
    pub host: String,
    /// the port on which the database is running
    #[arg(short, long, default_value_t = 5432)]
    pub port: u16,
    /// username to connect with
    #[arg(short, long, default_value = "postgres")]
    pub username: String,
    /// password for that username (don't provide a sensitive, real password)
    #[arg(short, long, default_value = "postgres")]
    pub password: String,
    /// path to write output to in json format
    #[arg(short, long)]
    pub output: PathBuf,
    /// the minimum number of downloads a package needs to be selected
    #[arg(short, long, default_value_t = 0)]
    pub min_downloads: i64,
    /// how to write the resulting data
    #[arg(short, long, default_value_t = OutputFormat::NDJSON)]
    pub format: OutputFormat,
    /// which ecosystems to pull from. Multiple inputs are acceptable
    pub ecosystems: Vec<EcosystemValue>,
}

#[cfg(feature = "ecosystem-dump")]
impl EcosystemDumpArgs {
    pub fn db_params(&self) -> DbConnectionInfo {
        DbConnectionInfo::new(&self.db_name, &self.host, self.port, &self.username, &self.password)
    }
    
    pub fn query_params(&self) -> EcosystemDumpParams {
        let ecos = self.ecosystems.iter().map(|val| val.clone().into()).collect::<HashSet<_>>();
        EcosystemDumpParams::new(self.min_downloads, ecos)
    }
}

#[derive(Debug, Clone, ValueEnum)]
pub enum ReportFormat {
    /// Excel spreadsheet workbook
    Xlsx,
    /// csv
    Csv,
    /// json (debugging purposes)
    Json,
}

impl Display for ReportFormat {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        match self {
            ReportFormat::Xlsx => f.write_str("xlsx"),
            ReportFormat::Csv => f.write_str("csv"),
            ReportFormat::Json => f.write_str("json"),
        }
    }
}

#[derive(Debug, Clone, Args)]
#[group(required = false, multiple = false)]
pub(crate) struct ReportFilter {
    /// only generate the reports included here
    #[arg(short, long)]
    include: Vec<String>,
    /// generate all reports except for the ones specified here
    #[arg(short, long)]
    exclude: Vec<String>
}

pub(crate) enum ReportFilterMode {
    None,
    Include(HashSet<String>),
    Exclude(HashSet<String>),
}

impl From<ReportFilter> for ReportFilterMode {
    fn from(value: ReportFilter) -> Self {
        if !value.include.is_empty() && !value.exclude.is_empty() {
            panic!("include and exclude cannot both be full");
        }

        if value.include.is_empty() && value.exclude.is_empty() {
            return Self::None
        }

        if !value.include.is_empty() {
            Self::Include(HashSet::from_iter(value.include.into_iter()))
        } else {
            Self::Exclude(HashSet::from_iter(value.exclude.into_iter()))
        }
    }
}

#[cfg(feature = "reporting")]
#[derive(Debug, Clone, Args)]
pub struct ReportGenArgs {
    /// what format to write the resulting format to
    #[arg(short, long, default_value_t = ReportFormat::Xlsx)]
    pub format: ReportFormat,
    /// where to write resulting
    #[arg(short, long)]
    pub output: PathBuf,
    /// Path to file that contains the report definition file
    #[arg(short, long)]
    pub def: PathBuf,
    #[command(flatten)]
    pub filter: ReportFilter,
    /// the database file to read from
    pub db_file: PathBuf,
}

#[derive(Debug, Clone, Args)]
pub struct SampleUniqueProjectsArgs {
    /// where to write sampled specs to
    #[arg(short, long)]
    pub output: PathBuf,
    /// how many packages to pull for each ecosystem
    #[arg(short, long)]
    pub count: usize,
    /// which ecosystems to pull projects from
    #[arg(short, long)]
    selected_ecosystems: Vec<SourceLanguageArg>,
    /// The path to DB file where already-processed packages are stored
    #[arg(short, long)]
    pub db_file: PathBuf,
    /// set of packages to sample form. This should be a collection of ndjson files containing
    /// packages specs
    pub spec_files: Vec<PathBuf>,
}

impl SampleUniqueProjectsArgs {
    pub fn selected_ecosystems(&self) -> HashSet<SourceLanguage> {
        self.selected_ecosystems.iter()
            .map(|ecosystem_value| ecosystem_value.clone().into())
            .collect()
    }
}
