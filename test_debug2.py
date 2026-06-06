import ast
import pandas as pd
import sys
sys.path.append("c:\\SistemaMigConta")
from backend.app.core.formula_parser import evaluate_formula_on_df

df = pd.DataFrame({
    'VENTA': [100, 200],
    'TIPO': ['A', 'B']
})

print("Testing SUMAR.SI.CONJUNTO...")
try:
    print(evaluate_formula_on_df(df, "SUMAR.SI.CONJUNTO(VENTA, TIPO, 'A')", None, 1))
except Exception as e:
    import traceback
    traceback.print_exc()

print("Testing directly inside loop...")
def test_parse():
    formula = "SUMAR.SI.CONJUNTO(VENTA, TIPO, 'A')"
    import re
    formula_clean = formula.upper().strip()
    formula_ast_str = formula_clean
    # some regex replacements happen in evaluate_formula_on_df...
    tree = ast.parse(formula_ast_str, mode='eval')
    node = tree.body
    def _get_name(n):
        if isinstance(n, ast.Name): return n.id.upper()
        elif isinstance(n, ast.Attribute): return _get_name(n.value) + "." + n.attr.upper()
        return ""
    func_id = _get_name(node.func)
    print("func_id:", repr(func_id))
    print("args len:", len(node.args))

test_parse()
