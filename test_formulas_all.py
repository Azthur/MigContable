import pandas as pd
import sys
sys.path.append("c:\\SistemaMigConta")
from backend.app.core.formula_parser import evaluate_formula_on_df

df = pd.DataFrame({
    'VENTA': [100, 200],
    'TIPO': ['A', 'B']
})

print("Testing SUMA...")
try:
    print(evaluate_formula_on_df(df, "SUMA(VENTA, 10)", None, 1))
except Exception as e:
    print("ERROR IN SUMA:", e)

print("Testing SI.CONJUNTO...")
try:
    print(evaluate_formula_on_df(df, "SI.CONJUNTO(TIPO=='A', 'Yes', TIPO=='B', 'No')", None, 1))
except Exception as e:
    print("ERROR IN SI.CONJUNTO:", e)

print("Testing SUMAR.SI.CONJUNTO...")
try:
    print(evaluate_formula_on_df(df, "SUMAR.SI.CONJUNTO(VENTA, TIPO, 'A')", None, 1))
except Exception as e:
    print("ERROR IN SUMAR.SI.CONJUNTO:", e)

print("Testing CONCAT_EXACTO...")
try:
    print(evaluate_formula_on_df(df, "CONCAT_EXACTO('a', CHR(10), 'b')", None, 1))
except Exception as e:
    print("ERROR IN CONCAT_EXACTO:", e)
