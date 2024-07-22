package edu.purdue.dualitylab.evaluation.util;

import java.util.*;
import java.util.stream.Collectors;

/**
 * A simple LRU bounded cache. You can hold only so many entries. Once full, the least-recently used
 * item is evicted
 * @param <K> Key type
 * @param <V> Value type
 */
public class BoundedCache<K, V> implements Map<K, V> {

    private static class Node<V> implements Comparable<Node<V>> {

        private final V item;
        private long lastUsed;

        public Node(V item) {
            this.item = item;
            this.lastUsed = -1; // this item hasn't been used
        }

        @Override
        public int compareTo(Node<V> vNode) {
            return Long.compare(this.lastUsed, vNode.getLastUsed());
        }

        public boolean isUsed() {
            return lastUsed >= 0;
        }

        public void updateUsed() {
            this.lastUsed = System.currentTimeMillis();
        }

        public V getItem() {
            return item;
        }

        public long getLastUsed() {
            return lastUsed;
        }
    }

    private final int maxEntries;
    private final Map<K, Node<V>> cache;

    public BoundedCache(int maxEntries) {
        this.maxEntries = maxEntries;
        this.cache = new HashMap<>();
    }

    @Override
    public int size() {
        return cache.size();
    }

    @Override
    public boolean isEmpty() {
        return cache.isEmpty();
    }

    @Override
    public boolean containsKey(Object o) {
        return cache.containsKey(o);
    }

    @Override
    public boolean containsValue(Object o) {
        return cache.containsValue(o);
    }

    @Override
    public V get(Object o) {
        Node<V> node = cache.get(o);
        if (node == null) {
            return null;
        }

        // show that this has been used lately
        node.updateUsed();

        return node.getItem();
    }

    @Override
    public V put(K k, V v) {
        // if we are not full, then just insert like usual
        Node<V> node = new Node<>(v);
        if (cache.size() < maxEntries) {
            Node<V> prev = cache.put(k, node);
            return prev == null ? null : prev.getItem();
        }

        // otherwise, we need to evict something
        Optional<K> leastRecentlyUsedKey = cache.entrySet().stream()
                .sorted(Entry.comparingByValue())
                .map(Map.Entry::getKey)
                .findFirst();

        leastRecentlyUsedKey.ifPresent(cache::remove);
        Node<V> prev = cache.put(k, node);
        return prev == null ? null : prev.getItem();
    }

    @Override
    public V remove(Object o) {
        Node<V> node = cache.remove(o);
        return node.getItem();
    }

    @Override
    public void putAll(Map<? extends K, ? extends V> map) {
        map.forEach(this::put);
    }

    @Override
    public void clear() {
        cache.clear();
    }

    @Override
    public Set<K> keySet() {
        return cache.keySet();
    }

    @Override
    public Collection<V> values() {
        return cache.values().stream().map(Node::getItem).toList();
    }

    @Override
    public Set<Entry<K, V>> entrySet() {
        return cache.entrySet().stream()
                .map(entry -> new AbstractMap.SimpleImmutableEntry<>(entry.getKey(), entry.getValue().getItem()))
                .collect(Collectors.toSet());
    }
}
