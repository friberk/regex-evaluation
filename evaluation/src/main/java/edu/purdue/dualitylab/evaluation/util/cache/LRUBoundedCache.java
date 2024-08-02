package edu.purdue.dualitylab.evaluation.util.cache;

import java.util.*;
import java.util.stream.Collectors;

/**
 * A simple LRU bounded cache. You can hold only so many entries. Once full, the least-recently used
 * item is evicted
 * @param <K> Key type
 * @param <V> Value type
 */
public class LRUBoundedCache<K, V> extends AbstractBoundedCache<K, V, LRUCacheNode<V>> {

    public LRUBoundedCache(int maxSize) {
        super(maxSize, new HashMap<>());
    }

    @Override
    protected LRUCacheNode<V> wrapValue(V value) {
        return new LRUCacheNode<>(value);
    }

    /**
     * Configurable procedure to select an item to evict. Returns the key of an item to evict. An item MUST be selected
     * for eviction.
     * @return The key of the item to evict
     */
    @Override
    protected K selectEvictKey() {
        return cacheImpl.entrySet().stream()
                .sorted(Entry.comparingByValue())
                .map(Map.Entry::getKey)
                .findFirst().orElseThrow(() -> new IllegalStateException("Cache was empty, so there are no items to evict"));
    }
}
