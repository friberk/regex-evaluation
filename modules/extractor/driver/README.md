
# driver

The driver module provides the actual driver binary that performs actions.

The main function parses command line arguments specified in the `args.rs` module. From there, the main function passes arguments down to specific driver commands.
Each command is specified in the `commands/` module. Each command takes its own argument block.

### Some Notable Commands
- `full_extract.rs` : provides command for extracting a sequence of packages
- `extract_dir.rs` : extract regexes and examples from a single directory, as provided from a cloned directory
- `report_gen.rs` : generate reports based on specifications using the regex database

### Other Notable Things
- The `extract/` module provides command static/dynamic extraction code that is shared by full extract and extract dir.
- `setup-extractors/` specifies our different static and dynamic extractors. Extractor maps essentially provide a static/dynamic extractor routine for each language. If you add new extractors, set them up here.
