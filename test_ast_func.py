import ast

def get_func_id(node):
    if isinstance(node, ast.Name):
        return node.id.upper()
    elif isinstance(node, ast.Attribute):
        return get_func_id(node.value) + "." + node.attr.upper()
    return ""

parsed = ast.parse("SUMAR.SI.CONJUNTO(A, B)", mode='eval')
print(get_func_id(parsed.body.func))
