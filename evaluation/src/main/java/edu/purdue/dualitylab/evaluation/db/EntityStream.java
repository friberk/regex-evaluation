package edu.purdue.dualitylab.evaluation.db;

import java.lang.reflect.InvocationTargetException;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.Spliterator;
import java.util.Spliterators;
import java.util.function.Consumer;

public class EntityStream<T> extends Spliterators.AbstractSpliterator<T> implements Spliterator<T> {

    private final ResultSet resultSet;
    private final Class<T> entityClass;

    protected EntityStream(ResultSet resultSet, Class<T> clazz) {
        super(Long.MAX_VALUE, Spliterator.ORDERED);
        this.resultSet = resultSet;
        this.entityClass = clazz;
    }

    @Override
    public boolean tryAdvance(Consumer<? super T> consumer) {
        try {
            // try to advance
            if (!resultSet.next()) {
                return false;
            }

            T entity = EntityMapper.toEntity(resultSet, entityClass);
            consumer.accept(entity);

            return true;
        } catch (SQLException | InstantiationException | IllegalAccessException | InvocationTargetException exe) {
            throw new RuntimeException(exe);
        }
    }
}
