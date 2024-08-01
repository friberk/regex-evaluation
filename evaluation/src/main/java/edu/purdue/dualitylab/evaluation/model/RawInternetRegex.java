package edu.purdue.dualitylab.evaluation.model;

import edu.purdue.dualitylab.evaluation.db.DbField;

public record RawInternetRegex(
        @DbField(name = "id") Long id,
        @DbField(name = "origin_id") Long originId,
        @DbField(name = "pattern") String pattern,
        @DbField(name = "origin_uri") String originUri
) {
}
