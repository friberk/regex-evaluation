package edu.purdue.dualitylab.evaluation.distance.ast;

import java.io.IOException;
import java.io.StreamTokenizer;
import java.io.StringReader;
import java.util.ArrayList;

public class Tree {
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

    public void traverse() {
        // put together an ordered list of node labels of the tree
        traverse(root, labels);
    }

    private static ArrayList<String> traverse(Node node, ArrayList<String> labels) {
        for (int i = 0; i < node.children.size(); i++) {
            labels = traverse(node.children.get(i), labels);
        }
//        System.out.println(node.label); // FOR TESTING
        labels.add(node.label);
        return labels;
    }

    public void index() {
        // index each node in the tree according to traversal method
        index(root, 0);
    }

    private static int index(Node node, int index) {
        for (int i = 0; i < node.children.size(); i++) {
            index = index(node.children.get(i), index);
        }
        index++;
        node.index = index;
        return index;
    }

    public void prepareForDistance() {
        if (hasBeenPrepared) {
            return;
        }

        this.index();
        this.l();
        this.keyroots();
        this.traverse();

        hasBeenPrepared = true;
    }

    public void l() {
        // put together a function which gives l()
        leftmost();
        leftmostChildren = l(root, new ArrayList<Integer>());
    }

    private ArrayList<Integer> l(Node node, ArrayList<Integer> l) {
        for (int i = 0; i < node.children.size(); i++) {
            l = l(node.children.get(i), l);
        }
        l.add(node.leftmost.index);
        return l;
    }

    private void leftmost() {
        leftmost(root);
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

    public void keyroots() {
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

    static int[][] TD;

    public static int ZhangShasha(Tree tree1, Tree tree2) {
        tree1.prepareForDistance();
        tree2.prepareForDistance();

        ArrayList<Integer> l1 = tree1.leftmostChildren;
        ArrayList<Integer> keyroots1 = tree1.keyroots;
        ArrayList<Integer> l2 = tree2.leftmostChildren;
        ArrayList<Integer> keyroots2 = tree2.keyroots;

        // space complexity of the algorithm
        TD = new int[l1.size() + 1][l2.size() + 1];

        // solve subproblems
        for (int i1 = 1; i1 < keyroots1.size() + 1; i1++) {
            for (int j1 = 1; j1 < keyroots2.size() + 1; j1++) {
                int i = keyroots1.get(i1 - 1);
                int j = keyroots2.get(j1 - 1);
                TD[i][j] = treedist(l1, l2, i, j, tree1, tree2);
            }
        }

        return TD[l1.size()][l2.size()];
    }

    private static int treedist(ArrayList<Integer> l1, ArrayList<Integer> l2, int i, int j, Tree tree1, Tree tree2) {
        int[][] forestdist = new int[i + 1][j + 1];

        // costs of the three atomic operations
        int Delete = 1;
        int Insert = 1;
        int Relabel = 1;

        forestdist[0][0] = 0;
        for (int i1 = l1.get(i - 1); i1 <= i; i1++) {
            forestdist[i1][0] = forestdist[i1 - 1][0] + Delete;
        }
        for (int j1 = l2.get(j - 1); j1 <= j; j1++) {
            forestdist[0][j1] = forestdist[0][j1 - 1] + Insert;
        }
        for (int i1 = l1.get(i - 1); i1 <= i; i1++) {
            for (int j1 = l2.get(j - 1); j1 <= j; j1++) {
                int i_temp = (l1.get(i - 1) > i1 - 1) ? 0 : i1 - 1;
                int j_temp = (l2.get(j - 1) > j1 - 1) ? 0 : j1 - 1;
                if ((l1.get(i1 - 1) == l1.get(i - 1)) && (l2.get(j1 - 1) == l2.get(j - 1))) {

                    int Cost = (tree1.labels.get(i1 - 1).equals(tree2.labels.get(j1 - 1))) ? 0 : Relabel;
                    forestdist[i1][j1] = Math.min(
                            Math.min(forestdist[i_temp][j1] + Delete, forestdist[i1][j_temp] + Insert),
                            forestdist[i_temp][j_temp] + Cost);
                    TD[i1][j1] = forestdist[i1][j1];
                } else {
                    int i1_temp = l1.get(i1 - 1) - 1;
                    int j1_temp = l2.get(j1 - 1) - 1;

                    int i_temp2 = (l1.get(i - 1) > i1_temp) ? 0 : i1_temp;
                    int j_temp2 = (l2.get(j - 1) > j1_temp) ? 0 : j1_temp;

                    forestdist[i1][j1] = Math.min(
                            Math.min(forestdist[i_temp][j1] + Delete, forestdist[i1][j_temp] + Insert),
                            forestdist[i_temp2][j_temp2] + TD[i1][j1]);
                }
            }
        }
        return forestdist[i][j];
    }
}
