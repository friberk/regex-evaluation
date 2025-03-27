use regex::{Regex};

/// parses the java version from a java home directory
pub(crate) fn parse_java_home_version(entry: &str) -> Option<u8> {
    // pull the version
    let version_extractor = Regex::new(r"^java-([^-]+)").expect("Regex should not fail to compile");
    let version_match_info = version_extractor.captures(entry)?;
    let version_str = version_match_info.get(1)?.as_str();

    parse_java_version(version_str)
}

/// parse a java version of either the form:
/// - 'version' e.g., 11
/// - 'semver' e.g. 1.8.0, 1.8
pub(crate) fn parse_java_version(version_str: &str) -> Option<u8> {
    // breakdown the version
    let complicated_version = Regex::new(r"^\d\.(\d+)(?:\.(\d+))?$").expect("Should not fail to compile");
    let simple_version = Regex::new(r"^\d+$").expect("Should not fail to compile");

    // try out the complicated version
    if let Some(capture_info) = complicated_version.captures(version_str) {
        let major_version_match = capture_info.get(1).expect("capture group 1 should be a thing");
        let major_version = major_version_match.as_str().parse::<u8>().expect("all digits should be parsable into a number");
        return Some(major_version);
    }

    // otherwise, try the not-complicated version
    if !simple_version.is_match(version_str) {
        return None;
    }

    let version = version_str.parse::<u8>().expect("if validated against regex, should succeed");
    Some(version)
}
