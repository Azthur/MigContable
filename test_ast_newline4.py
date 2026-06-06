import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
import sys
sys.path.append("c:\\SistemaMigConta")
from backend.app.core.formula_parser import evaluate_formula_on_df

df = pd.DataFrame({"URLVTA_pdf": ["http://a.pdf"], "URLVTA_XML": ["http://a.xml"]})
formula = "CONCAT('PDF: ', '\\n', URLVTA_pdf, '\\n', 'XML: ', '\\n', URLVTA_XML)"
# dummy engine and db
res = evaluate_formula_on_df(df, formula, None, 1)
print(repr(res.iloc[0]))
