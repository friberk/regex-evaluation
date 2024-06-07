package edu.purdue.dualitylab.evaluation.db;

import java.lang.annotation.Annotation;
import java.lang.reflect.Constructor;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Parameter;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.Arrays;
import java.util.Optional;

public class EntityMapper {
    public static <T> T toEntity(ResultSet row, Class<T> clazz) throws SQLException, InvocationTargetException, InstantiationException, IllegalAccessException {
        Constructor<?> constructor = selectConstructor(clazz.getConstructors()).orElseThrow();
        Parameter[] parameters = constructor.getParameters();
        Object[] paramValues = new Object[parameters.length];
        int i = 0;
        for (Parameter param : parameters) {
            Annotation[] annotations = param.getAnnotations();
            Optional<Annotation> annotation = findDbFieldAnnotation(annotations);
            String columName = annotation.isPresent() ? getColumnName(annotation.get()) : param.getName();
            Object value = getColumnValue(param, columName, row);
            paramValues[i++] = value;
        }

        return (T) constructor.newInstance(paramValues);
    }

    private static Optional<Annotation> findDbFieldAnnotation(Annotation[] annotations) {
        for (Annotation annotation : annotations) {
            if (annotation.annotationType().equals(DbField.class)) {
                return Optional.of(annotation);
            }
        }

        return Optional.empty();
    }

    private static String getColumnName(Annotation dbFieldAnnotation) {
        DbField dbField = (DbField) dbFieldAnnotation;
        return dbField.name();
    }

    private static Optional<Constructor<?>> selectConstructor(Constructor<?>[] constructors) {
        return Arrays.stream(constructors).findFirst();
    }

    private static Object getColumnValue(Parameter param, String columName, ResultSet row) throws SQLException {
        Class<?> paramType = param.getType();
        if (paramType.equals(String.class)) {
            return row.getString(columName);
        } else if (paramType.equals(Long.class)) {
            return row.getLong(columName);
        } else if (paramType.equals(Double.class)) {
            return row.getDouble(columName);
        } else if (paramType.equals(Boolean.class)) {
            return row.getBoolean(columName);
        } else {
            throw new IllegalArgumentException("Invalid parameter type: " + paramType);
        }
    }
}
