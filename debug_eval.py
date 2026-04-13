import sys, os
sys.path.append(os.getcwd())
import pandas as pd
from backend.app.core.database import dest_engine, DestSessionLocal
from backend.app.core.formula_parser import evaluate_formula_on_df
from sqlalchemy import text

db = DestSessionLocal()
with dest_engine.connect() as conn:
    df = pd.read_sql(text("SELECT * FROM vtaritem LIMIT 5"), conn)
    formula = "BUSCARX(C_Producto, CATALOGO_PRODUCTO_CATEGORIA, CATEGORIA, COD_PROD)"
    
    try:
        print("Evaluating...")
        res = evaluate_formula_on_df(df, formula, db, 4, default="")
        for idx, val in enumerate(res):
            print(f"Row {idx}: {df.iloc[idx]['C_Producto']} -> {val}")
    except Exception as e:
        import traceback
        traceback.print_exc()
