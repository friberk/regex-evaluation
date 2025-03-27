use std::collections::{HashMap, HashSet};
use std::error::Error;
use std::fs::File;
use std::io::{BufWriter, Write};
use std::path::PathBuf;
use std::process::{ExitCode};
use log::info;
use rand::seq::IteratorRandom;
use db::db_client::{RegexDBClient, RegexDBOperator};
use shared::package_spec::{PackageSpec, read_many_from_file, SourceLanguage};
use crate::args::SampleUniqueProjectsArgs;

pub fn sample_unique_projects(args: SampleUniqueProjectsArgs) -> Result<ExitCode, Box<dyn Error>> {

    let selected_languages = args.selected_ecosystems();
    info!("loading already processed packages from database...");
    let mut already_processed_packages = load_unique_already_processed_projects(args.db_file, &selected_languages)?;
    let total_packages: usize = already_processed_packages.values().map(|set| set.len()).sum();
    info!("loaded {} total packages", total_packages);
    let mut unique_packages = HashMap::<SourceLanguage, Vec<PackageSpec>>::new();

    for spec_file in args.spec_files {
        info!("reading packages from {}...", spec_file.display());
        read_many_from_file(&spec_file)
            ?.into_iter()
            .filter(|spec| selected_languages.contains(spec.language()))
            .for_each(|spec| {
                let language_seen_repos = already_processed_packages.get_mut(spec.language()).expect("language should always be present");
                if !language_seen_repos.contains(spec.repo()) {
                    language_seen_repos.insert(spec.repo().to_string());
                    if let Some(existing_sample) = unique_packages.get_mut(spec.language()) {
                        existing_sample.push(spec);
                    } else {
                        unique_packages.insert(spec.language().clone(), vec![spec]);
                    }
                }
            });
    }

    info!("loaded all packages. sampling...");

    // now, each unique packages for each project. we can sample and return that
    let mut sampled_package_specs = Vec::<PackageSpec>::new();
    let rng = &mut rand::thread_rng();
    for (_, packages) in unique_packages {
        let sample = packages.into_iter().choose_multiple(rng, args.count);
        sampled_package_specs.extend(sample);
    }


    // write everything out
    info!("writing output to {}...", args.output.display());
    let output_file = File::create(args.output)?;
    let mut writer = BufWriter::new(output_file);
    for spec in sampled_package_specs {
        let string_rep = serde_json::to_string(&spec)?;
        writeln!(writer, "{}", string_rep)?;
    }

    info!("done");

    Ok(ExitCode::SUCCESS)
}

fn load_unique_already_processed_projects(db_path: PathBuf, included_languages: &HashSet<SourceLanguage>) -> Result<HashMap<SourceLanguage, HashSet<String>>, Box<dyn Error>> {
    // get a set of already processed packages for each ecosystem
    let mut already_processed = HashMap::<SourceLanguage, HashSet<String>>::new();

    // load unique repos by project
    let db_client = RegexDBClient::new(db_path)?;
    RegexDBOperator::wrap(&db_client)
        .load_project_spec_repos()?
        .into_iter()
        .filter(|(lang, _)| included_languages.contains(&lang))
        .for_each(|(source_language, repo_url)| {
            if let Some(existing) = already_processed.get_mut(&source_language) {
                existing.insert(repo_url);
            } else {
                already_processed.insert(source_language, HashSet::from([repo_url]));
            }
        });

    Ok(already_processed)
}
