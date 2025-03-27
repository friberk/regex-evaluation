mod is_metachar_regex;
mod filter_regex;

use std::ffi::c_int;
use filter_regex::{filter_regex, filter_regex_func_flags, FILTER_REGEX_FUNC_NAME};
use rusqlite::{Connection, ffi};
use rusqlite::ffi::{SQLITE_ERROR, SQLITE_OK};
use log::error;
use crate::is_metachar_regex::{is_metachar_regex, is_metachar_regex_func_flags, IS_METACHAR_REGEX_FUNC_NAME};

#[no_mangle]
pub unsafe extern "C" fn sqlite3_extension_init(
    db: *mut ffi::sqlite3,
    _pz_err_msg: &mut &mut std::os::raw::c_char,
    p_api: *mut ffi::sqlite3_api_routines
) -> c_int {
    let connection = match Connection::extension_init2(db, p_api) {
        Ok(connection) => {
            connection
        }
        Err(err) => {
            error!("failed to initialize extension: {}", err);
            return rusqlite::ffi::SQLITE_ERROR
        }
    };

    initialize_extension(connection).unwrap_or_else(|err| {
        error!("failed to finish initializing extension: {}", err);
        SQLITE_ERROR
    })
}

fn initialize_extension(db: Connection) -> rusqlite::Result<c_int> {
    db.create_scalar_function(IS_METACHAR_REGEX_FUNC_NAME, 1, is_metachar_regex_func_flags(), is_metachar_regex)?;
    db.create_scalar_function(FILTER_REGEX_FUNC_NAME, 2, filter_regex_func_flags(), filter_regex)?;
    Ok(SQLITE_OK)
}
