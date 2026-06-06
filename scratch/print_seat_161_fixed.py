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
        if not sub:
            print("Subcategory 63 not found!")
            return
            
        with dest_engine.connect() as conn:
            query = 'SELECT * FROM "cntfacturadet" WHERE "company_id" = 4 AND "C_periodo" = \'2026\' AND "C_mes" = \'06\''
            df = pd.read_sql(query, conn)
            
        clave_columns = ['FacturaCabId']
        nasiento_base = 1
        df['nasiento'] = df.groupby(clave_columns, dropna=False).ngroup() + nasiento_base
        
        row_subset = df[df['FacturaCabId'] == 235]
        print(f"\nSubset of cntfacturadet for FacturaCabId=235 (len={len(row_subset)}):")
        print(row_subset[['Id', 'FacturaCabId', 'nasiento', 'CodCia', 'C_TipoDoc']])
        
        for linea in sub.lineas_asiento:
            if not linea.mapeo_detalle:
                continue
            temp_df = row_subset.copy()
            cond = getattr(linea, "condicion_aplicacion", None)
            if cond:
                try:
                    mask = evaluate_formula_on_df(temp_df, cond, db, 4, default=False)
                    mask = pd.to_numeric(mask, errors='coerce').fillna(0).astype(bool) | (mask.astype(str).str.strip().str.upper() == 'TRUE')
                    temp_df = temp_df[mask]
                except Exception as e:
                    print(f"Error evaluating condition '{cond}': {e}")
                    continue
            
            if temp_df.empty:
                print(f"Line {linea.orden} '{linea.nombre_linea}': Did not match.")
                continue
                
            print(f"\nLine {linea.orden} '{linea.nombre_linea}': Matched {len(temp_df)} rows.")
            # Eval detail formulas
            for db_field, formula in list(linea.mapeo_detalle.items())[:5]:
                val = evaluate_formula_on_df(temp_df, formula, db, 4, default="")
                print(f"  Field {db_field}: formula='{formula}' -> values={val.tolist()}")

    finally:
        db.close()

if __name__ == "__main__":
    main()
