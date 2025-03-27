use std::error::Error;
use std::fmt::{Display, Formatter};
use std::path::Path;
use libxml::parser::{Parser, XmlParseError};
use libxml::tree::Document;
use libxml::xpath::{Context};
use log::{debug};
use regex::Regex;

#[derive(Debug)]
pub(crate) enum PomError {
    /// some error happened
    IO(std::io::Error),
    XmlSyntax(XmlParseError),
    NoVersion,
    Other,
}

impl Display for PomError {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        match self {
            PomError::IO(err) => write!(f, "I/O Error: {}", err),
            PomError::XmlSyntax(err) => write!(f, "xml syntax error: {}", err),
            PomError::NoVersion => write!(f, "no version found"),
            PomError::Other => write!(f, "some other error occurred"),
        }
    }
}

impl Error for PomError {}

const DEFAULT_NS: &'static str = "http://maven.apache.org/POM/4.0.0";
const MAVEN_PROPERTIES_JAVA_VERSION_XPATH: &'static str = r"/pom:project/pom:properties/pom:java.version";
const MAVEN_PROPERTIES_COMPILER_SOURCE_VERSION_XPATH: &'static str = r"/pom:project/pom:properties/pom:maven.compiler.source";
const MAVEN_PROPERTIES_COMPILER_TARGET_VERSION_XPATH: &'static str = r"/pom:project/pom:properties/pom:maven.compiler.target";
const MAVEN_COMPILER_PLUGIN_SOURCE_VERSION_XPATH: &'static str = "/pom:project/pom:build//pom:plugins/pom:plugin[pom:artifactId='maven-compiler-plugin']/pom:configuration/pom:source";
const MAVEN_COMPILER_PLUGIN_TARGET_VERSION_XPATH: &'static str = "/pom:project/pom:build//pom:plugins/pom:plugin[pom:artifactId='maven-compiler-plugin']/pom:configuration/pom:source";

const XPATH_ORDER: [&'static str; 5] = [
    MAVEN_PROPERTIES_JAVA_VERSION_XPATH,
    MAVEN_PROPERTIES_COMPILER_SOURCE_VERSION_XPATH,
    MAVEN_PROPERTIES_COMPILER_TARGET_VERSION_XPATH,
    MAVEN_COMPILER_PLUGIN_SOURCE_VERSION_XPATH,
    MAVEN_COMPILER_PLUGIN_TARGET_VERSION_XPATH,
];

pub(crate) fn extract_pom_version(pom_path: &Path) -> Result<String, PomError> {
    let parser = Parser::default();
    let document = parser.parse_file(pom_path.to_string_lossy().as_ref())
        .map_err(|err| PomError::XmlSyntax(err))?;
    
    extract_pom_version_document(document)
}

/// actual implementation for parsing the info out of the document. This is for testing purposes
fn extract_pom_version_document(document: Document) -> Result<String, PomError> {
    let xpath_context = Context::new(&document)
        .map_err(|_| PomError::Other)?;

    xpath_context.register_namespace("pom", DEFAULT_NS)
        .map_err(|_| PomError::Other)?;


    for xpath in XPATH_ORDER {
        let Ok(result) = xpath_context.evaluate(xpath) else {
            debug!("xpath [{}] produced no results, moving onto the next...", xpath);
            continue
        };

        let version_text = result.to_string();
        if version_text.trim().is_empty() {
            debug!("xpath [{}] produced empty text, continuing...", xpath);
            continue;
        }

        let resolved_version = is_property_reference(&version_text)
            // figure out if this is a property reference and resolve it if so
            .and_then(|property_name| try_resolve_property_reference(&xpath_context, property_name))
            // if it's not, then we found a version, so go with that
            .unwrap_or(version_text);

        return Ok(resolved_version)
    }

    return Err(PomError::NoVersion)
}

fn is_property_reference(version: &str) -> Option<&str> {
    let extractor = Regex::new(r"^\$\{([^}]+)}$").expect("Pattern should not fail to compile");
    let capture_info = extractor.captures(version)?;
    let property_name = capture_info.get(1)?;
    debug!("provided version '{}' is actually a property reference to '{}'", version, property_name.as_str());
    Some(property_name.as_str())
}

/// checks if the provided "java version" is really a reference to a property. If it is, it'll try
/// to read that property and return that value instead
fn try_resolve_property_reference(xpath_ctx: &Context, property: &str) -> Option<String> {
    let xpath = format!("/pom:project/pom:properties/pom:{}", property);
    match xpath_ctx.evaluate(&xpath) {
        Ok(hit) => {
            let property_value = hit.to_string();
            if property_value.trim().is_empty() {
                None
            } else {
                debug!("evaluated property '{}' to '{}'", property, property_value);
                Some(property_value)
            }
        },
        Err(_) => None
    }
}

#[cfg(test)]
mod tests {
    use libxml::parser::Parser;
    use crate::dynamic_extractor_manager::java::pom_info::{extract_pom_version_document};

    #[test]
    fn finds_java_version_in_properties() {
        let contents = r#"
        <?xml version="1.0" encoding="UTF-8"?>
        <project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
            <properties>
                <java.version>1.8</java.version>
            </properties>
        </project>"#;
        let parser = Parser::default();
        let document = parser.parse_string(contents).expect("Should successfully parse");

        let version = extract_pom_version_document(document).expect("Should successfully get version");
        assert_eq!(version, "1.8");
    }

    #[test]
    fn resolves_property_reference() {
        let contents = r#"
        <?xml version="1.0" encoding="UTF-8"?>
        <project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
            <properties>
                <java-version>1.8</java-version>
                <java.version>${java-version}</java.version>
            </properties>
        </project>"#;
        let parser = Parser::default();
        let document = parser.parse_string(contents).expect("Should successfully parse");

        let version = extract_pom_version_document(document).expect("Should successfully get version");
        assert_eq!(version, "1.8");
    }
}
