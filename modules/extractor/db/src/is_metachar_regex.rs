use rusqlite::Connection;
use rusqlite::functions::{Context, FunctionFlags};
use rusqlite::types::{FromSqlError, ValueRef};
use shared::regex_metachars::pattern_has_metacharacters;

pub const IS_METACHAR_REGEX_FUNC_NAME: &'static str = "IS_METACHAR_REGEX";

#[inline]
pub fn load_is_metachar_regex_function(db: &Connection) -> rusqlite::Result<()> {
    db.create_scalar_function(IS_METACHAR_REGEX_FUNC_NAME, 1, FunctionFlags::SQLITE_DETERMINISTIC | FunctionFlags::SQLITE_DIRECTONLY, is_metachar_regex)
}

fn is_metachar_regex(context: &Context) -> rusqlite::Result<bool> {
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
