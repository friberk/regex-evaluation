use rusqlite::functions::{Context, FunctionFlags};
use rusqlite::types::{FromSqlError, ValueRef};

use shared::regex_metachars::pattern_has_metacharacters;

pub(crate) const IS_METACHAR_REGEX_FUNC_NAME: &'static str = "IS_METACHAR_REGEX";
pub(crate) fn is_metachar_regex_func_flags() -> FunctionFlags {
    FunctionFlags::SQLITE_DETERMINISTIC | FunctionFlags::SQLITE_INNOCUOUS
}

pub(crate) fn is_metachar_regex(context: &Context) -> rusqlite::Result<bool> {
    assert_eq!(context.len(), 1);
    let has_meta = match context.get_raw(0) {
        ValueRef::Text(value) => {
            let pattern_str = std::str::from_utf8(value).map_err(|_| FromSqlError::InvalidType)?;
            let has_meta = pattern_has_metacharacters(pattern_str);
            has_meta
        }
        _ => false,
    };
    
    Ok(has_meta)
}
