DROP TABLE project_usage_and_pattern_counts;
CREATE TEMPORARY TABLE project_usage_and_pattern_counts AS
SELECT project_id, project_spec.name AS project_name, COUNT(regex_source_usage.id) as usage_count, COUNT(DISTINCT regex_entity.pattern) as pattern_count FROM regex_source_usage
INNER JOIN project_spec ON regex_source_usage.project_id = project_spec.id
INNER JOIN regex_entity ON regex_source_usage.regex_id = regex_entity.id AND regex_entity.static AND regex_entity.dynamic
GROUP BY project_id
ORDER BY usage_count DESC;

SELECT * FROM project_usage_and_pattern_counts ORDER BY pattern_count DESC;

DROP TABLE regex_entity_extraction_categories;
CREATE TEMPORARY TABLE regex_entity_extraction_categories AS
SELECT regex_entity.id,
       CASE regex_entity.static
           WHEN TRUE
               THEN CASE regex_entity.dynamic
                        WHEN TRUE
                            THEN 4 -- static and dynamic
                        ELSE
                            3 -- static but not dynamic
               END
           ELSE
               CASE regex_entity.dynamic
                   WHEN TRUE
                       THEN 2 -- dynamic but not static
                   ELSE
                       1 -- neither
                   END
           END AS status
FROM regex_entity;

SELECT COUNT(id) FROM regex_entity;

SELECT COUNT(id) static_is_true FROM regex_entity WHERE static = TRUE;
SELECT COUNT(id) dynamic_is_true FROM regex_entity WHERE dynamic = TRUE;

SELECT status, COUNT(status) as count FROM regex_entity_extraction_categories
GROUP BY status;

-- contains information about which project originated each regex
CREATE TEMPORARY TABLE candidate_regexes_and_origins AS
SELECT regex_entity.id as regex_id, project_spec.id as project_id, regex_source_usage.id as source_usage_id FROM regex_source_usage
INNER JOIN regex_entity ON regex_source_usage.regex_id = regex_entity.id AND regex_entity.static IS TRUE AND regex_entity.dynamic IS TRUE
INNER JOIN project_spec ON regex_source_usage.project_id = project_spec.id;

SELECT regex_entity.pattern, candidate_regexes_and_origins.project_id, source_usage_id, subject, func FROM regex_subject
INNER JOIN candidate_regexes_and_origins ON candidate_regexes_and_origins.project_id = regex_subject.project_id AND candidate_regexes_and_origins.regex_id = regex_subject.regex_id
INNER JOIN regex_entity ON candidate_regexes_and_origins.regex_id = regex_entity.id
ORDER BY regex_entity.id;

-- determine reuse of regexes across packages
-- find the regexes that have usages found in multiple projects
DROP TABLE IF EXISTS patterns_across_projects;
CREATE TEMPORARY TABLE patterns_across_projects AS
SELECT regex_id, regex_entity.pattern, COUNT(DISTINCT project_id) as distinct_project_id_count FROM regex_source_usage
INNER JOIN regex_entity ON regex_source_usage.regex_id = regex_entity.id
WHERE pattern GLOB '*[.^$*+?\]\[\\|(){}]*'
GROUP BY regex_id
ORDER BY distinct_project_id_count DESC;

SELECT * FROM patterns_across_projects
ORDER BY distinct_project_id_count DESC;

SELECT * FROM patterns_across_projects
WHERE distinct_project_id_count > 50;

-- static with examples
SELECT distinct_project_id_count AS project_reuse_count, COUNT(distinct_project_id_count) AS frequency
FROM patterns_across_projects
INNER JOIN regex_entity ON regex_id = regex_entity.id
WHERE regex_entity.static IS TRUE AND regex_entity.dynamic IS TRUE
GROUP BY distinct_project_id_count
ORDER BY project_reuse_count DESC;

-- static without examples
SELECT distinct_project_id_count AS project_reuse_count, COUNT(distinct_project_id_count) AS frequency
FROM patterns_across_projects
INNER JOIN regex_entity ON regex_id = regex_entity.id
WHERE regex_entity.static IS TRUE AND regex_entity.dynamic IS FALSE
GROUP BY distinct_project_id_count
ORDER BY project_reuse_count DESC;

-- anything
SELECT distinct_project_id_count AS project_reuse_count, COUNT(distinct_project_id_count) AS frequency
FROM patterns_across_projects
INNER JOIN regex_entity ON regex_id = regex_entity.id
GROUP BY distinct_project_id_count
ORDER BY project_reuse_count DESC;

-- regexes with metacharacters
SELECT COUNT(DISTINCT pattern) as regexes_with_metachars FROM regex_entity
WHERE pattern GLOB '*[.^$*+?\]\[\\|(){}]*'
    AND static IS TRUE;

-- select regexes with test suites
-- find all regexes with examples that were statically extracted and contain metacharacters
-- group the results by the regex, the function that produced the example, and the count of distinct examples

SELECT regex_entity.id, regex_subject.func, COUNT(DISTINCT regex_subject.subject) as unique_string_count
FROM regex_subject
INNER JOIN regex_entity ON regex_entity.id = regex_id
WHERE
    regex_entity.pattern GLOB '*[.^$*+?\]\[\\|(){}]*' AND  -- take only patterns that have meta characters in them
    regex_entity.static = TRUE                             -- take only patterns that were found statically
GROUP BY regex_entity.pattern, regex_subject.func
ORDER BY regex_entity.id;

-- Collect information on the frequency of lengths of subject strings in the database
DROP TABLE IF EXISTS regex_subject_lengths;
CREATE TEMPORARY TABLE regex_subject_lengths AS
SELECT regex_subject.id, LENGTH(regex_subject.subject) AS subject_len
FROM regex_subject
INNER JOIN regex_entity ON regex_entity.id = regex_id
WHERE
    regex_entity.pattern GLOB '*[.^$*+?\]\[\\|(){}]*' AND  -- take only patterns that have meta characters in them
    regex_entity.static = TRUE                             -- take only patterns that were found statically
GROUP BY regex_subject.subject
ORDER BY subject_len;

SELECT subject_len, COUNT(subject_len)
FROM regex_subject_lengths
GROUP BY subject_len
ORDER BY subject_len;

SELECT func, AVG(subject_len) as avg_subject_len
FROM regex_subject
INNER JOIN regex_entity ON regex_entity.id = regex_id
WHERE
    regex_entity.pattern GLOB '*[.^$*+?\]\[\\|(){}]*' AND  -- take only patterns that have meta characters in them
    regex_entity.static = TRUE                             -- take only patterns that were found statically
GROUP BY regex_subject.func
ORDER BY avg_subject_len DESC;