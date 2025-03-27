
-- Create Project Spec table
BEGIN TRANSACTION;

-- Models a source project
CREATE TABLE IF NOT EXISTS project_spec (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    -- the project name
    name TEXT NOT NULL,
    -- the github repo URL for this project
    repo TEXT NOT NULL,
    -- a license associated with this project, if any
    license TEXT,
    -- the source language for this project
    language TEXT,
    -- the start count for this project
    downloads INTEGER DEFAULT 0,
    -- ensure that projects are unique by name and repository
    UNIQUE (name, repo)
);

-- in the case that there are multiple projects hosted inside of the same repository, record those packages but don't
-- keep them around in the same way
CREATE TABLE IF NOT EXISTS duplicate_project_specs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    -- the project name
    name TEXT NOT NULL,
    -- the start count for this project
    downloads INTEGER DEFAULT 0,
    -- what parent this is a duplicate of
    parent_project_id INTEGER,
    FOREIGN KEY (parent_project_id) REFERENCES project_spec(id)
);

-- loc info for each project
CREATE TABLE IF NOT EXISTS project_loc_info (
    -- the project that this loc info describes
    project_id INTEGER NOT NULL,
    -- number of files
    files INTEGER NOT NULL,
    -- number of blank lines
    blank INTEGER NOT NULL,
    -- lines of comments
    comment INTEGER NOT NULL,
    -- lines of code
    code INTEGER NOT NULL,
    FOREIGN KEY (project_id) REFERENCES project_spec(id)
);

-- models a specific regex, which is just a pattern and its flags
CREATE TABLE IF NOT EXISTS regex_entity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    -- the actual regex pattern
    pattern TEXT NOT NULL,
    -- any flags associated with this pattern
    flags TEXT,
    -- determines if the regex was found statically
    static BOOLEAN DEFAULT FALSE,
    -- determines if this regex was found dynamically. Set this flag when inserting a subject and there was no
    -- corresponding statically extracted regex. False means it was statically extracted, true means it was dynamically
    -- extracted and there was no static regex with the same pattern
    dynamic BOOLEAN DEFAULT FALSE,
    -- all regexes should be a unique pattern-flags combination
    UNIQUE (pattern, flags)
);

-- models a specific usage of a regex. The same regex can be used across multiple files and projects
CREATE TABLE IF NOT EXISTS regex_source_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    -- where in the source file this usage occurred
    line_no INTEGER NOT NULL,
    -- which file this usage occurred in, relative to the project root
    source_file TEXT NOT NULL,
    -- the commit of the project at the origin
    commit_hash TEXT,
    -- foreign key reference to the project that this usage occurred in
    project_id INTEGER,
    -- the regex found at this location
    regex_id INTEGER,
    FOREIGN KEY (project_id) REFERENCES project_spec(id),
    FOREIGN KEY (regex_id) REFERENCES regex_entity(id),
    -- each usage should be unique
    UNIQUE (line_no, source_file, commit_hash, project_id, regex_id)
);

-- represents a subject example used with a regex
CREATE TABLE IF NOT EXISTS regex_subject (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    -- the regex that this subject was run on
    regex_id INTEGER NOT NULL,
    -- the project id that this subject came from
    project_id INTEGER NOT NULL,
    -- the actual subject
    subject TEXT NOT NULL,
    -- TRUE if this was a positive match, false otherwise
    matches BOOLEAN DEFAULT FALSE,
    -- RegExp function that was called
    func TEXT NOT NULL,
    FOREIGN KEY (regex_id) REFERENCES regex_entity(id),
    FOREIGN KEY (project_id) REFERENCES project_spec(id),
    -- Each subject should be unique by regex and project. the same subject can exist:
    --  * for the same regex, but across different projects
    --  * for the same project, but different regexes
    UNIQUE (subject, regex_id, project_id)
);

CREATE TABLE IF NOT EXISTS project_processing_report (
    -- the relevant project
    project_id INTEGER,
    -- a simple text status of what happened
    status TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES project_spec(id),
    UNIQUE (project_id)
);

COMMIT;
