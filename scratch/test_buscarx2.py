import sys
import pandas as pd
import numpy as np
sys.path.append('c:/SistemaMigConta')
from backend.app.core.database import DestSessionLocal
from backend.app.core.formula_parser import evaluate_formula_on_df

db = DestSessionLocal()
company_id = 1

df = pd.DataFrame({'C_car': ['N/AB050000015', 'N/AB050000015']})
res = evaluate_formula_on_df(df, "BUSCARX_EXT(C_car, ccbrgdoc, C_car, fchdoc)", db, company_id)
print("Result of BUSCARX_EXT on 'N/AB050000015' (company_id=1):")
print(res)

