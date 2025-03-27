use std::error::Error;
use std::fs::File;
use std::io;
use std::io::{BufReader, BufWriter, Write};
use std::path::Path;
use log::{debug};
use shared::error::ExtractorError;

pub fn preprocess_npm_project_directory(npm_proj_dir: &Path) -> Result<(), Box<dyn Error>> {
    let pkg_file = npm_proj_dir.join("package.json");
    if !pkg_file.exists() {
        return Err(ExtractorError::Other(format!("Package {} has no package.json in it", npm_proj_dir.display())).into())
    }

    configure_linters_to_ignore(npm_proj_dir)
}

fn string_replace(subject: &mut String, to_replace: &str, replacement: &str) {
    if let Some(replacement_start_iter) = subject.find(to_replace) {
        subject.replace_range(replacement_start_iter..replacement_start_iter + to_replace.len(), replacement);
    }
}

fn have_gitignore_style_file_ignore_all_js(file_path: &Path) -> io::Result<()> {
    let file = File::create(file_path)?;
    let mut ignore_file = BufWriter::new(file);
    writeln!(ignore_file, "\n\n# Ignore all JS files\n# (added for dynamic instrumentation)\n**/*.js")
}

fn configure_eslint_to_ignore_all(npm_proj_dir: &Path) -> io::Result<()> {
    have_gitignore_style_file_ignore_all_js(&npm_proj_dir.join(".eslintignore"))
}

fn configure_standard_to_ignore_all(npm_proj_dir: &Path) -> io::Result<()> {
    have_gitignore_style_file_ignore_all_js(&npm_proj_dir.join(".gitignore"))
}

fn configure_jscs_to_ignore_all(npm_proj_dir: &Path) -> Result<(), Box<dyn Error>> {
    let config_file = npm_proj_dir.join(".jscsrc");
    let mut cfg = if let Ok(file) = File::open(&config_file) {
        let reader = BufReader::new(file);
        serde_json::from_reader(reader).unwrap_or_default()
    } else {
        serde_json::json!({})
    };

    let exclude_files = if let Some(excluded_files) = cfg.get_mut("excludeFiles") {
        excluded_files
    } else {
        cfg.as_object_mut().unwrap().insert("excludeFiles".to_string(), serde_json::Value::Array(vec![]));
        cfg.as_object_mut().unwrap().get_mut("excludeFiles").unwrap()
    };
    
    exclude_files.as_array_mut().unwrap().push(serde_json::Value::String("**/*.js".to_string()));

    let cfg_file_out = File::create(&config_file)?;
    serde_json::to_writer_pretty(cfg_file_out, &cfg)?;
    Ok(())
}

fn remove_linter_from_package_json_stages(npm_proj_dir: &Path, stages: &[String]) -> Result<(), Box<dyn Error>> {
    let package_path = npm_proj_dir.join("package.json");
    let package_file = File::open(&package_path)?;
    let mut reader = BufReader::new(package_file);
    let mut cfg: serde_json::Value = serde_json::from_reader(&mut reader)?;

    if let Some(scripts) = cfg.get_mut("scripts") {
        if let serde_json::Value::Object(scripts_obj) = scripts {
            for stage in stages {
                if let Some(stage_script) = scripts_obj.get_mut(stage) {
                    if let Some(stage_text) = stage_script.as_str() {
                        let mut stage_text = stage_text.to_string();
                        string_replace(&mut stage_text, "npm run lint && ", "");
                        string_replace(&mut stage_text, "npm run lint;", "");
                        *stage_script = serde_json::Value::String(stage_text);
                    }
                }
            }
        }
    }

    let output_file = File::create(&package_path)?;
    let mut pkg_file_out = BufWriter::new(output_file);
    serde_json::to_writer_pretty(&mut pkg_file_out, &cfg)?;
    Ok(())
}

fn configure_linters_to_ignore(npm_proj_dir: &Path) -> Result<(), Box<dyn Error>> {
    debug!("Removing linter from package.json stages...");
    remove_linter_from_package_json_stages(npm_proj_dir, &["build".to_string(), "test".to_string(), "unit".to_string()])?;
    debug!("Configuring linter: eslint");
    configure_eslint_to_ignore_all(npm_proj_dir)?;
    debug!("Configuring linter: standard");
    configure_standard_to_ignore_all(npm_proj_dir)?;
    debug!("Configuring linter: JSCS");
    configure_jscs_to_ignore_all(npm_proj_dir)?;
    debug!("Done configuring linters");
    Ok(())
}
