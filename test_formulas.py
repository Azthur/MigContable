import sys
sys.path.append('c:\\SistemaMigConta')
from backend.app.core.formula_parser import evaluate_formula_on_df
import pandas as pd
from unittest.mock import MagicMock
import re

df = pd.DataFrame({'COL1': ['P-12345', '12345', 'A-444', '0000', 'X-99']})

# Using '' inside double quotes to represent empty string
formula1 = "SI.CONJUNTO(ENCONTRAR('-', COL1)>0, EXTRAER(COL1, 1, RESTA(ENCONTRAR('-', COL1), 1)), ENCONTRAR('-', COL1)=0, '')"
formula2 = "SI.CONJUNTO(ENCONTRAR('-', COL1)>0, EXTRAER(COL1, SUMA(ENCONTRAR('-', COL1), 1), 100), ENCONTRAR('-', COL1)=0, COL1)"

db = MagicMock()

def debug_pre(formula_str):
    print("0:", formula_str)
    formula_str = formula_str.strip()
    print("1:", formula_str)
    formula_str = re.sub(r'["\']([^"\']+)["\'][\'"]+', r"'\1'", formula_str)
    print("2:", formula_str)
    formula_str = re.sub(r'[\'"]+([^"\']+)["\']', r"'\1'", formula_str)
    print("3:", formula_str)
    formula_ast_str = re.sub(r'(?<![=<>!])=(?![=])', '==', formula_str)
    print("4:", formula_ast_str)
    return formula_ast_str

print("Debug pre formula1:", debug_pre(formula1))
try:
    res1 = evaluate_formula_on_df(df, formula1, db, 1)
    print("Formula 1 results:")
    print(res1)
except Exception as e:
    print(f"Error 1: {e}")

print("Debug pre formula2:", debug_pre(formula2))
try:
    res2 = evaluate_formula_on_df(df, formula2, db, 1)
    print("Formula 2 results:")
    print(res2)
except Exception as e:
    print(f"Error 2: {e}")
