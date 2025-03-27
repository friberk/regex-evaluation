use rusqlite::functions::{Context, FunctionFlags};
use rusqlite::types::{FromSqlError, ValueRef};

use shared::regex_metachars::pattern_has_metacharacters;

pub(crate) const FILTER_REGEX_FUNC_NAME: &'static str = "FILTER_REGEX_PATTERN";
pub(crate) fn filter_regex_func_flags() -> FunctionFlags {
    FunctionFlags::SQLITE_DETERMINISTIC | FunctionFlags::SQLITE_INNOCUOUS
}

pub(crate) fn filter_regex(context: &Context) -> rusqlite::Result<bool> {
    assert_eq!(context.len(), 2);

    let min_length_arg = context.get::<i64>(1)?;

    let has_meta = match context.get_raw(0) {
        ValueRef::Text(value) => {
            let pattern_str = std::str::from_utf8(value).map_err(|_| FromSqlError::InvalidType)?;
            evaluate_pattern(pattern_str, min_length_arg)
        }
        _ => false,
    };
    
    Ok(has_meta)
}

fn evaluate_pattern(pattern: &str, min_length_arg: i64) -> bool {
    if !pattern_has_metacharacters(pattern) {
        return false;
    }

    let min_length = min_length_arg.clamp(0, i64::MAX) as usize;
    if pattern.len() < min_length {
        return false;
    }

    true
}

#[cfg(test)]
mod test {
    use crate::is_interesting_regex::evaluate_pattern;

    #[test]
    fn accepts_long_with_metachars() {
        assert!(evaluate_pattern("[a-z]+", 4));
    }

    #[test]
    fn rejects_too_short() {
        assert!(!evaluate_pattern("[a-z]+", 8));
    }

    #[test]
    fn rejects_no_metas() {
        assert!(!evaluate_pattern("application/json", 2));
    }

    #[test]
    fn accepts_when_length_not_set() {
        assert!(evaluate_pattern(r"\s", -1));
    }
}
