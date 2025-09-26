from metrics.syntactic_similarity.ast import get_distinct_features, regex_to_ast

def count_distinct_features(regex):
    ast = regex_to_ast(regex)
    count, features = get_distinct_features(ast)
    return count, features

