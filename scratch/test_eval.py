import sys
import pandas as pd
sys.path.append('c:/SistemaMigConta')
from backend.app.core.database import DestSessionLocal
from backend.app.core.formula_parser import evaluate_formula_on_df

db = DestSessionLocal()

df = pd.DataFrame({'fchdoc': [pd.Timestamp('2026-06-01 00:00:00')]})
print("Initial df:")
print(df)

res = evaluate_formula_on_df(df, "LEFT(fchdoc, 10)", db, 5)
print("Result of LEFT:")
print(res)

df["C_fechaEmision"] = res
print("Final df:")
print(df)
