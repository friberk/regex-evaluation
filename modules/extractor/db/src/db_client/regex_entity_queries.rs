use rusqlite::{Connection, Error, named_params};
use shared::regex_entity::RegexEntity;

#[inline]
pub fn insert_new_regex_entity(connection: &Connection, entity: &RegexEntity) -> Result<usize, Error> {
    insert_new_regex_entity_raw(connection, entity.pattern(), entity.flags(), true, false)
}

pub fn insert_new_regex_entity_raw<StrT: AsRef<str>>(connection: &Connection, pattern: StrT, flags: StrT, static_: bool, dynamic: bool) -> Result<usize, Error> {
    // insert a new regex_entity. if it already exists, then this
    let mut insert_stmt = connection.prepare_cached("INSERT OR IGNORE INTO regex_entity (pattern, flags, static, dynamic) VALUES (:pattern, :flags, :static, :dynamic)")?;
    insert_stmt.execute(
        named_params! {
            ":pattern": pattern.as_ref(),
            ":flags": flags.as_ref(),
            ":static": static_,
            ":dynamic": dynamic
        }
    )
}

pub fn set_regex_entity_dynamic_flag<StrT: AsRef<str>>(connection: &Connection, pattern: StrT, dynamic: bool) -> Result<usize, Error> {
    connection.execute(
        "UPDATE regex_entity SET dynamic=:dynamic WHERE pattern=:pattern",
        named_params! {
            ":dynamic": dynamic,
            ":pattern": pattern.as_ref()
        }
    )
}

pub fn set_regex_entity_static_flag<StrT: AsRef<str>>(connection: &Connection, pattern: StrT, static_: bool) -> Result<usize, Error> {
    connection.execute(
        "UPDATE regex_entity SET static=:static WHERE pattern=:pattern",
        named_params! {
            ":static": static_,
            ":pattern": pattern.as_ref()
        }
    )
}
