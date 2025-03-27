mod args;
mod py_conversion;

use std::error::Error;
use std::io::{BufRead, BufReader, BufWriter, ErrorKind, Write};
use std::os::unix::net::UnixListener;
use std::path::Path;
use std::process::ExitCode;
use clap::Parser;
use log::{debug, error, info, LevelFilter};
use pyo3::{Bound, PyResult, Python};
use pyo3::types::{PyAnyMethods, PyList, PyListMethods, PyModule};
use shared::regex_entity::ParsedRegexEntity;
use crate::args::Args;
use crate::py_conversion::convert_py_regex_entity;

fn python_main(py: Python, args: Args) -> PyResult<()> {
    // setup the current path
    let module = match import_static_extractor(&py, &args.extractor_path) {
        Ok(module) => {
            info!("successfully imported static extractor module");
            module
        },
        Err(err) => {
            error!("error while importing static extractor module from path '{}': {}", args.extractor_path.to_string_lossy(), err);
            return Err(err);
        }
    };
    let parse_fn = module.getattr("parse_file")?;

    let socket_listener = match UnixListener::bind(&args.listen_path) {
        Ok(listener) => {
            info!("successfully bound listener");
            listener
        }
        Err(err) => {
            error!("failed to bind listener to path '{}': {}", args.listen_path.to_string_lossy(), err);
            return Err(err.into());
        }
    };
    info!("listening for connections on {}", args.listen_path.to_string_lossy());

    let server_result = loop {
        info!("Starting to listen for next connection...");
        let (client, _) = match socket_listener.accept() {
            Ok(info) => info,
            Err(err) => break match err.kind() {
                ErrorKind::Interrupted => Ok(()),
                _ => Err(err)
            },
        };

        info!("accepted client");

        let mut buffered_client_writer = BufWriter::new(&client);
        let mut buffered_client_reader = BufReader::new(&client);

        let mut line_buffer = String::default();
        let mut parsed_entities = Vec::<ParsedRegexEntity>::new();
        let mut is_test_connection = true;
        while let Ok(bytes_read) = buffered_client_reader.read_line(&mut line_buffer) {
            if bytes_read == 0 && is_test_connection {
                break;
            }
            
            // if we got here, then we made it past the first iteration without EOFing i.e. we read data
            is_test_connection = false;
            
            debug!("received raw line: '{}'", line_buffer);
            let trimmed_line = line_buffer.trim();
            if trimmed_line.is_empty() {
                break;
            }

            let args = (trimmed_line,);
            let results = parse_fn.call1(args)?;
            let results_list = results.downcast_into::<PyList>()?;

            // if there are no entities, then there is nothing to do from here on
            info!("parsed {} entities from {}", results_list.len(), trimmed_line);
            if results_list.is_empty() {
                line_buffer.clear();
                continue;
            }

            // pass all entities across python/rust boundary
            for result_item in results_list.iter() {
                let entity = convert_py_regex_entity(result_item, trimmed_line)?;
                parsed_entities.push(entity);
            }
            
            info!("parsed {} entities from {}", parsed_entities.len(), trimmed_line);

            line_buffer.clear();
        }

        if !is_test_connection {
            serde_json::to_writer(&mut buffered_client_writer, &parsed_entities).expect("Serialization should always work");
            buffered_client_writer.write_all(&['\r' as u8, '\n' as u8])?;
            buffered_client_writer.flush().unwrap();
        }
        info!("client connection closed");
    };

    match server_result {
        Ok(_) => {
            info!("signaled server to stop. server is shutting down")
        }
        Err(err) => {
            error!("error occurred during server execution: {}", err)
        }
    }

    Ok(())
}

fn main() -> Result<ExitCode, Box<dyn Error>> {

    env_logger::builder()
        .filter_level(LevelFilter::Info)
        .parse_default_env()
        .init();

    let args = Args::parse();

    match Python::with_gil(move |py| python_main(py, args)) {
        Ok(_) => {
            info!("server terminated successfully");
            Ok(ExitCode::SUCCESS)
        }
        Err(err) => {
            error!("server interpreter exited with error: {}", err);
            Ok(ExitCode::FAILURE)
        }
    }
}

fn import_static_extractor<'py>(py: &'py Python, extractor_path: &Path) -> PyResult<Bound<'py, PyModule>> {

    let extractor_path = extractor_path.canonicalize()?;

    let sys_module = py.import_bound("sys")?;
    let path_attr = sys_module.getattr("path")?;
    let path_attr_list = path_attr.downcast_into::<PyList>()?;

    // add the parent to the lookup path
    path_attr_list.insert(0, extractor_path.parent())?;

    let module_file_name = extractor_path.file_name().expect("extractor module should have been a file, not a directory").to_string_lossy();
    let module_name = extractor_path.extension()
        .and_then(|ostr| ostr.to_str()) // convert operating system string to normal string
        .and_then(|ext| module_file_name.strip_suffix(ext)) // if there is an extension, remove it
        .map(|without_extension| &without_extension[..without_extension.len() - 1])
        .unwrap_or(module_file_name.as_ref()); // get the module name with no extension or the original filename if there was no extension

    py.import_bound(module_name)
}
