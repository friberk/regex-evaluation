package edu.institution.lab.evaluation.util.cache;

/**
 * A general cache node. A cache nodes must produce left value and be sorted
 * @param <ValueT>
 */
public interface CacheNode<ValueT> {
    /**
     * Gets the value held within the cache node
     * @return Cached value
     */
    ValueT getValue();

    /**
     * Optional hook called when the node is used
     */
    default void onUse() {}
}
