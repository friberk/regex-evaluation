package edu.purdue.dualitylab.evaluation.util.cache;

public class LRUCacheNode<ValueT> implements CacheNode<ValueT>, Comparable<LRUCacheNode<ValueT>> {

    private static final int UNUSED = -1;

    private final ValueT value;
    private long lastUsed;

    public LRUCacheNode(ValueT value) {
        this.value = value;
        this.lastUsed = UNUSED;
    }

    @Override
    public ValueT getValue() {
        return value;
    }

    @Override
    public void onUse() {
        this.markUsed();
    }

    /**
     * Mark that this node has been accessed recently
     */
    public void markUsed() {
        this.lastUsed = System.nanoTime();
    }

    @Override
    public int compareTo(LRUCacheNode<ValueT> valueTLRUCacheNode) {
        return Long.compare(this.lastUsed, valueTLRUCacheNode.lastUsed);
    }
}
