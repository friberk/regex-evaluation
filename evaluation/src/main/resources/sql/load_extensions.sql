
-- load extension
SELECT load_extension(?1, 'sqlite3_extension_init');

-- create view on DB
CREATE VIEW IF NOT EXISTS regex_entity_static_metachars AS
SELECT * FROM regex_entity
WHERE
    IS_METACHAR_REGEX(pattern) AND
    regex_entity.pattern = TRUE;
