SELECT id, name, ecosystem, normalized_licenses[1], repository_url, COALESCE(downloads, 0) as downloads
FROM packages
WHERE
    ecosystem = $2 AND
    coalesce(repository_url, '') != '' AND
    COALESCE(downloads, 0) >= $1;