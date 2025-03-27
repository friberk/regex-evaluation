
const REGEX_METACHARS: [char; 14] = [
    '.', '^', '$', '*', '+', '?', ']', '[', '\\', '|', '(', ')', '{', '}'
];

/// simple function to test if a pattern has regex metacharacters and is therefore worth
/// investigating
pub fn pattern_has_metacharacters<StrT: AsRef<str>>(pattern: StrT) -> bool {
    pattern.as_ref().chars()
        .any(|ch| REGEX_METACHARS.contains(&ch))
}