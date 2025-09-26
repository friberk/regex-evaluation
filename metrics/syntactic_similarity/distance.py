from zss import Node as ZssNode, simple_distance
from metrics.syntactic_similarity.ast import ASTNode, regex_to_ast
from typing import Tuple, Dict

def convert_to_zss(node: ASTNode) -> Tuple[ZssNode, int]:
    """
    Recursively convert our ASTNode to a zss.Node.
    We set the zss node label to include the node type and, if present, its text.
    """
    if node is None:
        return ZssNode(("EPS", None)), 1

    z_node = ZssNode((node.node_type, node.text))
    tree_size = 1
    for child in getattr(node, "children", []):
        z_child, child_size = convert_to_zss(child)
        z_node.addkid(z_child)
        tree_size += child_size
    return z_node, tree_size

def regex_ast_distance(regex1: str, regex2: str) -> Dict[str, float]:
    """
    Tree edit distance between regex ASTs (syntactic, not language distance).
    Returns raw distance and a [0,1] normalization by (n1 + n2).
    """
    try:
        t1 = regex_to_ast(regex1)
        t2 = regex_to_ast(regex2)
        z1, n1 = convert_to_zss(t1)
        z2, n2 = convert_to_zss(t2)

        d = float(simple_distance(z1, z2))
        denom = max(1, n1 + n2 - 2)  # keeps normalized value in [0,1], -2 because we don't count the root nodes
        return {
            "ast_edit_distance": d,
            "normalized_ast_edit_distance": d / denom,
        }
    except Exception:
        return {
            "ast_edit_distance": None,
            "normalized_ast_edit_distance": None,
        }
