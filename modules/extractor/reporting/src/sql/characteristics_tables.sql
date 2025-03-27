
BEGIN TRANSACTION;

--------------------------------------
-- Sheet: Package Processing Report --
--------------------------------------

-- how did each processing go down
CREATE TEMPORARY TABLE project_processing_summary_report AS
SELECT status, project_spec.language AS source_language, COUNT(status) as status_count
FROM project_processing_report
INNER JOIN project_spec ON project_spec.id = project_id
GROUP BY project_processing_report.status, project_spec.language
ORDER BY status_count DESC;

----------------------------------
-- Sheet: Packages With Regexes --
----------------------------------

-- Figure out how many regexes are in each project
-- select unique-by-regex source usages grouped by project.
-- then, count the usages
CREATE TEMPORARY TABLE packages_with_regexes AS
SELECT project_spec.name AS project_name, project_spec.language, COUNT(DISTINCT regex_source_usage.regex_id) as unique_static_regex_count
FROM regex_source_usage
INNER JOIN regex_entity ON regex_entity.id = regex_id
INNER JOIN project_spec ON project_spec.id = project_id
WHERE
    regex_entity.pattern GLOB '*[.^$*+?\]\[\\|(){}]*' AND  -- take only patterns that have meta characters in them
    regex_entity.static = TRUE                             -- take only patterns that were found statically
GROUP BY project_id
ORDER BY unique_static_regex_count DESC;

------------------------------------
-- Sheet: Regexes Across Projects --
------------------------------------

-- Figure out how many statically extracted regexes with metacharacters occur across projects

-- describes how many times a regex occurs across multiple projects
CREATE TEMPORARY TABLE regex_reuse_across_projects_count AS
SELECT regex_entity.id AS regex_id, COUNT(DISTINCT regex_source_usage.project_id) AS unique_project_count
FROM regex_source_usage
INNER JOIN regex_entity ON regex_entity.id = regex_id
INNER JOIN project_spec ON project_spec.id = project_id
WHERE
    regex_entity.pattern GLOB '*[.^$*+?\]\[\\|(){}]*' AND  -- take only patterns that have meta characters in them
    regex_entity.static = TRUE                             -- take only patterns that were found statically
GROUP BY regex_id
ORDER BY unique_project_count DESC;

-- Find regexes that occur statically across multiple projects
CREATE TEMPORARY TABLE regexes_reused_across_projects AS
SELECT regex_entity.id as regex_id, regex_entity.pattern, unique_project_count
FROM regex_reuse_across_projects_count
INNER JOIN regex_entity ON regex_entity.id = regex_id
WHERE
    unique_project_count > 1
ORDER BY unique_project_count DESC;

-- Find the frequency of static regex project recurrence, i.e., how many regexes occur in one, two, three, or more projects
CREATE TEMPORARY TABLE project_recurrence_frequency AS
SELECT unique_project_count, COUNT(unique_project_count) as frequency
FROM regex_reuse_across_projects_count
GROUP BY unique_project_count
ORDER BY frequency DESC;

-------------------------------------
-- Sheet: Regexes With Test Suites --
-------------------------------------

-- Figure out how many regexes have test suites
CREATE TEMPORARY TABLE regex_testsuite_size AS
SELECT regex_entity.id, regex_entity.pattern, COUNT(DISTINCT regex_subject.subject) as unique_subject_count
FROM regex_subject
INNER JOIN regex_entity ON regex_entity.id = regex_id
WHERE
    regex_entity.pattern GLOB '*[.^$*+?\]\[\\|(){}]*' AND  -- take only patterns that have meta characters in them
    regex_entity.static = TRUE                             -- take only patterns that were found statically
GROUP BY regex_entity.id
ORDER BY unique_subject_count DESC;

-- figure out where those test suites come from: from multiple packages? or just one
CREATE TEMPORARY TABLE regex_testsuite_cross_project_origins AS
SELECT regex_entity.id, COUNT(DISTINCT project_id) unique_originating_projects, COUNT(DISTINCT regex_subject.subject) as unique_subject_count
FROM regex_subject
INNER JOIN regex_entity ON regex_entity.id = regex_id
WHERE
    regex_entity.pattern GLOB '*[.^$*+?\]\[\\|(){}]*' AND  -- take only patterns that have meta characters in them
    regex_entity.static = TRUE                             -- take only patterns that were found statically
GROUP BY regex_entity.id
ORDER BY regex_entity.id;

COMMIT;
