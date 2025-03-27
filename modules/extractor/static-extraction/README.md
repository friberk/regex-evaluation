
# static-extraction

This crate provides a client/server system for static extractors. The idea is that, for each language, we have some sort of static extractor server. The protocol look something like this

1. static extractor server starts listening for connections on a socket (unix or tcp, depending on the language)
2. client connects to the static extractor server
3. client writes CLRF (`\r\n`) delimited file paths for the server to parse. When there are no more files, an empty line is sent (just `\r\n`)
4. the server parses the file and extracts regexes. For each extracted regex, a record is sent over, containing the regex and source information
5. The client collects and combines all records received from the server
6. The client disconnects

This crate provides three majors things:
- `ExtractorConnection` - client for extractor server. Use this to send paths and send dones
- `ExtractorInfo` - specifies how to start and connect to and extractor server.
- `ExtractorManager` - takes an extractor info and starts the respective extractor server. This object performs a few roles:
  - Execute and maintain the static extractor server
  - Create connections for this extractor
  - Destroy the extractor server using RAII
 
`extract_package` provides an interface for actually walking through a package's source and performing extraction operations
