import pandas as pd
import sys
sys.path.append("c:\\SistemaMigConta")
from backend.app.core.formula_parser import evaluate_formula_on_df

df = pd.DataFrame({
    'VENTA': [100, 200],
    'TIPO': ['A', 'B']
})

print("Testing SUMAR.SI.CONJUNTO...")
import ast
from backend.app.core.formula_parser import eval_ast
parsed = ast.parse("SUMAR.SI.CONJUNTO(VENTA, TIPO, 'A')", mode='eval')
print("parsed body is:", type(parsed.body))
print("func_id is inside parser:", getattr(parsed.body, 'func', None))

try:
    print(evaluate_formula_on_df(df, "SUMAR.SI.CONJUNTO(VENTA, TIPO, 'A')", None, 1))
except Exception as e:
    import traceback
    traceback.print_exc()
