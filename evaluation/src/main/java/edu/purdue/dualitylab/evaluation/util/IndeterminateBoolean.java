package edu.purdue.dualitylab.evaluation.util;

import java.util.Optional;

public enum IndeterminateBoolean {
    TRUE,
    FALSE,
    UNDETERMINED;

    public static IndeterminateBoolean fromBoolean(boolean b) {
        return b ? TRUE : FALSE;
    }

    public boolean coerceToBoolean() {
        return this == IndeterminateBoolean.TRUE;
    }

    public Optional<Boolean> toOptionalBoolean() {
        return switch (this) {
            case TRUE -> Optional.of(true);
            case FALSE -> Optional.of(false);
            case UNDETERMINED -> Optional.empty();
        };
    }
}
