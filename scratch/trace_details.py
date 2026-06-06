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
            # We don't filter out anything just to see the processing
            query = 'SELECT * FROM "cntfacturadet" WHERE "company_id" = 4 AND "C_periodo" = \'2026\' AND "C_mes" = \'06\''
            df = pd.read_sql(query, conn)
            
        print(f"Loaded {len(df)} source records.")
        if df.empty:
            return

        # Simulating nasiento column calculation
        clave_columns = ['FacturaCabId']
        nasiento_base = 1
        df['nasiento'] = df.groupby(clave_columns, dropna=False).ngroup() + nasiento_base
        print(f"Computed nasiento in df. Unique seats: {df['nasiento'].nunique()}")

        # Simulating lines loop
        lineas = sub.lineas_asiento
        print(f"Total lines to process: {len(lineas)}")
        
        diariol_entries = []
        for linea in lineas:
            if not linea.mapeo_detalle:
                print(f"Line {linea.orden}: No detail map, skipping.")
                continue
                
            temp_df = df.copy()
            cond = getattr(linea, "condicion_aplicacion", None)
            if cond:
                mask = evaluate_formula_on_df(temp_df, cond, db, 4, default=False)
                mask = pd.to_numeric(mask, errors='coerce').fillna(0).astype(bool) | (mask.astype(str).str.strip().str.upper() == 'TRUE')
                temp_df = temp_df[mask]
                print(f"Line {linea.orden} '{linea.nombre_linea}': Cond '{cond}' matched {len(temp_df)} rows.")
            else:
                print(f"Line {linea.orden} '{linea.nombre_linea}': No cond matched {len(temp_df)} rows.")
                
            if temp_df.empty:
                continue
                
            # Eval detail formulas
            for db_field, formula in linea.mapeo_detalle.items():
                temp_df[f"_calc_{db_field}"] = evaluate_formula_on_df(temp_df, formula, db, 4, default="")
                
            if linea.nivel == "CABECERA":
                temp_df = temp_df.drop_duplicates(subset=['nasiento'])
                print(f"  Level CABECERA -> deduped to {len(temp_df)} rows.")
                
            # Print calculated columns for first row to see if anything is wrong
            first_idx = temp_df.index[0]
            row_calc = temp_df.loc[first_idx]
            print(f"  First matched row (idx={first_idx}) _calc_ values:")
            for k in linea.mapeo_detalle.keys():
                col = f"_calc_{k}"
                print(f"    {k}: mapped from '{linea.mapeo_detalle[k]}' -> {row_calc.get(col)}")

    finally:
        db.close()

if __name__ == "__main__":
    main()
