
DROP TABLE IF EXISTS regex_entity_extraction_categories;
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

SELECT status, COUNT(status) as count FROM regex_entity_extraction_categories
GROUP BY status;
