package edu.institution.lab.evaluation.distance.ast;

import java.io.IOException;
import java.io.StreamTokenizer;
import java.io.StringReader;
import java.util.ArrayList;

public final class Tree {

    private static Node parseString(Node node, StreamTokenizer tokenizer) throws IOException {
        node.label = tokenizer.sval;
        tokenizer.nextToken();
        if (tokenizer.ttype == '(') {
            tokenizer.nextToken();
            do {
                node.children.add(parseString(new Node(), tokenizer));
            } while (tokenizer.ttype != ')');
            tokenizer.nextToken();
        }
        return node;
    }

    private static ArrayList<String> traverse(Node node, ArrayList<String> labels) {
        for (int i = 0; i < node.children.size(); i++) {
            labels = traverse(node.children.get(i), labels);
        }
//        System.out.println(node.label); // FOR TESTING
        labels.add(node.label);
        return labels;
    }

    private static int index(Node node, int index) {
        for (int i = 0; i < node.children.size(); i++) {
            index = index(node.children.get(i), index);
        }
        index++;
        node.index = index;
        return index;
    }

    private static void leftmost(Node node) {
        if (node == null)
            return;
        for (int i = 0; i < node.children.size(); i++) {
            leftmost(node.children.get(i));
        }
        if (node.children.isEmpty()) {
            node.leftmost = node;
        } else {
            node.leftmost = node.children.get(0).leftmost;
        }
    }

    private Node root;
    // function l() which gives the leftmost child
    private ArrayList<Integer> leftmostChildren;
    // list of keyroots, i.e., nodes with a left child and the tree root
    private final ArrayList<Integer> keyroots;
    // list of the labels of the nodes used for node comparison
    private final ArrayList<String> labels;
    private boolean hasBeenPrepared;

    // the following constructor handles preorder notation. E.g., f(a b(c))
    public Tree(Node root) {
        this.root = root;
        this.leftmostChildren = new ArrayList<>();
        this.keyroots = new ArrayList<>();
        this.labels = new ArrayList<>();
        this.hasBeenPrepared = false;
    }

    public Tree(String s) throws IOException {
        this(new Node());
        StreamTokenizer tokenizer = new StreamTokenizer(new StringReader(s));
        tokenizer.nextToken();
        root = parseString(root, tokenizer);
        if (tokenizer.ttype != StreamTokenizer.TT_EOF) {
            throw new RuntimeException("Leftover token: " + tokenizer.ttype);
        }
    }

    public void traverse() {
        // put together an ordered list of node labels of the tree
        traverse(root, labels);
    }

    public void index() {
        // index each node in the tree according to traversal method
        index(root, 0);
    }

    public void prepareForDistance() {
        if (hasBeenPrepared) {
            return;
        }

        this.index();
        this.l();
        this.computeKeyroots();
        this.traverse();

        hasBeenPrepared = true;
    }

    public void l() {
        // put together a function which gives l()
        computeLeftmost();
        leftmostChildren = l(root, new ArrayList<Integer>());
    }

    private ArrayList<Integer> l(Node node, ArrayList<Integer> l) {
        for (int i = 0; i < node.children.size(); i++) {
            l = l(node.children.get(i), l);
        }
        l.add(node.leftmost.index);
        return l;
    }

    private void computeLeftmost() {
        leftmost(root);
    }

    public void computeKeyroots() {
        // calculate the keyroots
        for (int i = 0; i < leftmostChildren.size(); i++) {
            int flag = 0;
            for (int j = i + 1; j < leftmostChildren.size(); j++) {
                if (leftmostChildren.get(j) == leftmostChildren.get(i)) {
                    flag = 1;
                }
            }
            if (flag == 0) {
                this.keyroots.add(i + 1);
            }
        }
    }

    public ArrayList<Integer> getLeftmostChildren() {
        return leftmostChildren;
    }

    public ArrayList<Integer> getKeyroots() {
        return keyroots;
    }

    public ArrayList<String> getLabels() {
        return labels;
    }
}
