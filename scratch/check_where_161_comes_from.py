import sys
import os
import pandas as pd
from sqlalchemy import create_engine, text

sys.path.append("c:\\SistemaMigConta")
os.environ["POSTGRES_CONNECTION_STRING"] = "postgresql://postgres:postgres@localhost:5434/migconta_db"

from backend.app.core.database import DestSessionLocal, dest_engine
from backend.app.models.models import MapeoSubcategoria
from backend.app.core.formula_parser import evaluate_formula_on_df

def main():
    db = DestSessionLocal()
    try:
        sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == 63).first()
        
        with dest_engine.connect() as conn:
            # Load row Id = 469
            df_row = pd.read_sql('SELECT * FROM "cntfacturadet" WHERE "Id" = 469', conn)
            
        print("Row 469 values:")
        for col in df_row.columns:
            val = df_row.loc[0, col]
            if val is not None and val != "":
                print(f"  {col}: {repr(val)}")
                
        clave_columns = ['FacturaCabId']
        nasiento_base = 1
        df_row['nasiento'] = 161  # Set it to match the seat
        
        print("\nEvaluating all lines of subcategory 63 on row 469:")
        for linea in sub.lineas_asiento:
            if not linea.mapeo_detalle:
                continue
            temp_df = df_row.copy()
            cond = getattr(linea, "condicion_aplicacion", None)
            if cond:
                mask = evaluate_formula_on_df(temp_df, cond, db, 4, default=False)
                mask = pd.to_numeric(mask, errors='coerce').fillna(0).astype(bool) | (mask.astype(str).str.strip().str.upper() == 'TRUE')
                matched = mask.iloc[0]
            else:
                matched = True
                
            print(f"Line {linea.orden} '{linea.nombre_linea}': Condition={repr(cond)} -> Matched: {matched}")

    finally:
        db.close()

if __name__ == "__main__":
    main()
