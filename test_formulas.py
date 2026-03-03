import os
import sys
sys.path.append("c:\\SistemaMigConta")
import pandas as pd
from backend.app.core.formula_parser import evaluate_formula_on_df

df = pd.DataFrame({"coddoc": ["BOLE", "FACT"], "nbase1": [100.0, 200.0]})
print("Test 1:", evaluate_formula_on_df(df, "'121201'", None, 1).tolist())
print("Test 2:", evaluate_formula_on_df(df, "121201", None, 1).tolist())
print("Test 3:", evaluate_formula_on_df(df, "nbase1", None, 1).tolist())
print("Test 4:", evaluate_formula_on_df(df, "CONCAT('Vta', coddoc)", None, 1).tolist())
print("Test 5:", evaluate_formula_on_df(df, "CONCAT(SI.CONJUNTO(coddoc='N/A', LEFT(coddoc, 1), coddoc='N/A', LEFT(coddoc, 1)),LEFT(coddoc, 3))", None, 1).tolist())
try:
    print("Test 6:", evaluate_formula_on_df(df, "", None, 1).tolist())
except Exception as e:
    print("Test 6 Exception:", e)
