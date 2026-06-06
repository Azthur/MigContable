import pandas as pd
import ast
import sys
sys.path.append("c:\\SistemaMigConta")
from backend.app.core.formula_parser import evaluate_formula_on_df

df = pd.DataFrame({
    "URLVTA_pdf": ["http://pdf"],
    "URLVTA_XML": ["http://xml"],
    "URLVTA_CDR": ["http://cdr"],
    "ESTADO_VTA": ["OK"]
})

formula_ast_str = r'CONCAT("PDF: ", " | \n", URLVTA_pdf, " | \n", "XML: ", " | \n", URLVTA_XML, " | \n", "CDR: ", " | \n", URLVTA_CDR, " | \n", "ESTADO COMPROBANTE: ", " | \n", ESTADO_VTA)'

res = evaluate_formula_on_df(df, formula_ast_str, None, 1)
print(repr(res.iloc[0]))
