from zss import Node as ZssNode, simple_distance
from .ast import ASTNode, regex_to_ast
from typing import Tuple

def convert_to_zss(node: ASTNode) -> Tuple[ZssNode, int]:
    """
    Recursively convert our ASTNode to a zss.Node.
    We set the zss node label to include the node type and, if present, its text.
    """
    if node is None:
        return ZssNode("None"), 0

    label = node.node_type if node.text is None else f"{node.node_type}:{node.text}"
    z_node = ZssNode(label)
    tree_size = 1

    for child in node.children:
        z_child, child_size = convert_to_zss(child)
        if z_child is not None:
            z_node.addkid(z_child)
            tree_size += child_size

    return z_node, tree_size

def edit_distance(regex1: str, regex2: str) -> float:
    """
    Compute the tree edit distance between the ASTs for two regexes.
    """
    tree1 = regex_to_ast(regex1)
    tree2 = regex_to_ast(regex2)
    ztree1, ztree1_size = convert_to_zss(tree1)
    ztree2, ztree2_size = convert_to_zss(tree2)
    distance = simple_distance(ztree1, ztree2)

    # Normalize the distance by the number of nodes in the larger tree
    normalization_factor = max(ztree1_size, ztree2_size, 1)
    normalized_ast_edit_distance = distance / normalization_factor

    return {
        "ast_edit_distance": distance,
        "normalized_ast_edit_distance": normalized_ast_edit_distance
    }
