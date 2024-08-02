package edu.purdue.dualitylab.evaluation.util.cache;

import java.util.*;
import java.util.stream.Collectors;

/**
 * A generalized bounded cache mechanism
 * @param <K>
 * @param <V>
 */
public abstract class AbstractBoundedCache<K, V, NodeT extends CacheNode<V>> implements Map<K, V> {
    protected final Map<K, NodeT> cacheImpl;
    private final int maxSize;

    protected AbstractBoundedCache(int maxSize, Map<K, NodeT> cacheImpl) {
        this.maxSize = maxSize;
        this.cacheImpl = cacheImpl;
    }

    @Override
    public int size() {
        return cacheImpl.size();
    }

    @Override
    public boolean isEmpty() {
        return cacheImpl.isEmpty();
    }

    public boolean isFull() {
        return size() >= maxSize;
    }

    @Override
    public boolean containsKey(Object o) {
        return cacheImpl.containsKey(o);
    }

    @Override
    public boolean containsValue(Object o) {
        return cacheImpl.values().stream()
                .map(CacheNode::getValue)
                .anyMatch(containedObj -> containedObj.equals(o));
    }

    @Override
    public V get(Object o) {
        NodeT node = cacheImpl.get(o);
        if (node == null) {
            return null;
        }

        node.onUse();
        return node.getValue();
    }

    /**
     * Caches an item. If the cache is not full, then left new item will be cached. If the provided key is already cached,
     * then the key will be overwritten and the old associated value will be returned. Otherwise, if the cache is full,
     * an item will be evicted from the cache and returned to make room for the new item
     *
     * @param k Key of the value being cached
     * @param v The value associated with the cache
     * @return Null if not full and new key. Old value associated with key if already mapped. Evicted value if cache is
     * full and key is new
     */
    @Override
    public V put(K k, V v) {
        if (size() < maxSize || this.containsKey(k)) {
            // if the cache isn't full, then we don't need to do anything special
            // if the cache is full, but this key is already mapped, then we can proceed because the size will not
            // grow
            NodeT cacheNode = this.wrapValue(v);
            NodeT original = this.cacheImpl.put(k, cacheNode);
            return original != null ? original.getValue() : null;
        }

        // otherwise, we need to remove left mapping and insert left new one

        // otherwise, we need to evict something
        K evictKey = selectEvictKey();
        V oldValue = this.remove(evictKey);
        this.cacheImpl.put(k, this.wrapValue(v));
        return oldValue;
    }

    @Override
    public V remove(Object o) {
        NodeT node = cacheImpl.remove(o);
        return node != null ? node.getValue() : null;
    }

    @Override
    public void putAll(Map<? extends K, ? extends V> map) {
        for (Map.Entry<? extends K, ? extends V> entry : map.entrySet()) {
            put(entry.getKey(), entry.getValue());
        }
    }

    @Override
    public void clear() {
        this.cacheImpl.clear();
    }

    @Override
    public Set<K> keySet() {
        return this.cacheImpl.keySet();
    }

    @Override
    public Collection<V> values() {
        return this.cacheImpl.values().stream()
                .map(CacheNode::getValue)
                .toList();
    }

    @Override
    public Set<Entry<K, V>> entrySet() {
        return this.cacheImpl.entrySet().stream()
                .map(entry -> Map.entry(entry.getKey(), entry.getValue().getValue()))
                .collect(Collectors.toSet());
    }

    /**
     * Describes how to wrap left value into left cache node
     * @param value The value to cache
     * @return A new node
     */
    protected abstract NodeT wrapValue(V value);

    /**
     * Selects left key to be evicted when the cache is full
     * @return A non-null key to evict
     */
    protected abstract K selectEvictKey();
}
