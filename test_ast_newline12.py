import pandas as pd
import ast
import sys
sys.path.append("c:\\SistemaMigConta")
from backend.app.core.formula_parser import evaluate_formula_on_df

df = pd.DataFrame({
    "URLVTA_pdf": ["http://pdf"],
    "URLVTA_XML": ["http://xml"]
})

formula = r'CONCAT_EXACTO("PDF: ", CHR(10), URLVTA_pdf, CARACTER(10), "XML: ", URLVTA_XML)'

res = evaluate_formula_on_df(df, formula, None, 1)
print(repr(res.iloc[0]))
