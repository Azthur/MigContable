import sys
import os
import pandas as pd
from sqlalchemy import create_engine, text

# Setup python path and connection
sys.path.append("c:\\SistemaMigConta")
os.environ["POSTGRES_CONNECTION_STRING"] = "postgresql://postgres:postgres@localhost:5434/migconta_db"

from backend.app.core.database import DestSessionLocal, dest_engine
from backend.app.models.models import MapeoSubcategoria
from backend.app.core.formula_parser import evaluate_formula_on_df

def main():
    db = DestSessionLocal()
    try:
        sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == 63).first()
        if not sub:
            print("Subcategory 63 not found!")
            return
            
        print("Reading source data for 2026-06...")
        with dest_engine.connect() as conn:
            query = 'SELECT * FROM "cntfacturadet" WHERE "company_id" = 4 AND "C_periodo" = \'2026\' AND "C_mes" = \'06\''
            df = pd.read_sql(query, conn)
            
        print(f"Loaded {len(df)} source records.")
        if df.empty:
            return

        print("\nEvaluating each mapping line condition:")
        for idx, line in enumerate(sub.lineas_asiento):
            if not line.mapeo_detalle:
                print(f"Line {line.orden} ({line.nombre_linea}): No mapeo_detalle, skipping.")
                continue
            
            temp_df = df.copy()
            cond = getattr(line, "condicion_aplicacion", None)
            if cond:
                try:
                    mask = evaluate_formula_on_df(temp_df, cond, db, 4, default=False)
                    mask = pd.to_numeric(mask, errors='coerce').fillna(0).astype(bool) | (mask.astype(str).str.strip().str.upper() == 'TRUE')
                    matched_df = temp_df[mask]
                    print(f"Line {line.orden} ({line.nombre_linea}): Condition='{cond}' -> Matched {len(matched_df)} of {len(df)} rows.")
                    if len(matched_df) > 0:
                        # Print some sample match values
                        print(f"  Matched row indices: {list(matched_df.index)}")
                except Exception as e:
                    print(f"Line {line.orden} ({line.nombre_linea}): Error evaluating condition '{cond}': {e}")
            else:
                print(f"Line {line.orden} ({line.nombre_linea}): No condition -> Matched all {len(temp_df)} rows.")

    finally:
        db.close()

if __name__ == "__main__":
    main()
