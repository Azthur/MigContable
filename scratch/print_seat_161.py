import sys
import os

sys.path.append("c:\\SistemaMigConta")
os.environ["POSTGRES_CONNECTION_STRING"] = "postgresql://postgres:postgres@localhost:5434/migconta_db"

from backend.app.core.database import DestSessionLocal
from backend.app.models.models import MapeoSubcategoria
from backend.app.api.endpoints.mapeo import _generate_subcategoria_cf_diariol

def main():
    db = DestSessionLocal()
    try:
        sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == 63).first()
        if not sub:
            print("Subcategory 63 not found!")
            return
            
        # Reset subcategory control value first
        db.execute(text("UPDATE mapeo_subcategorias SET last_generated_control_value = NULL, asiento_inicial = 1 WHERE id = 63"))
        db.commit()
        
        # We subclass/intercept the diariol_entries list to capture it before validation/insert
        print("Running generator...")
        # Since _generate_subcategoria_cf_diariol inserts details, we can query them from memory.
        # But wait! We can just modify the script to print what diariol_entries are generated.
        # Let's import and run a custom run that replicates the loop and prints details for nasiento = 161.
        
        # Read source data
        from backend.app.core.database import dest_engine
        import pandas as pd
        with dest_engine.connect() as conn:
            query = 'SELECT * FROM "cntfacturadet" WHERE "company_id" = 4 AND "C_periodo" = \'2026\' AND "C_mes" = \'06\''
            df = pd.read_sql(query, conn)
            
        clave_columns = ['FacturaCabId']
        nasiento_base = 1
        df['nasiento'] = df.groupby(clave_columns, dropna=False).ngroup() + nasiento_base
        
        # We know from the previous trace that some rows had validation errors. Let's trace the lines for FacturaCabId = 235 (which corresponds to nasiento = 161)
        row_subset = df[df['FacturaCabId'] == 235]
        print(f"\nSubset of cntfacturadet for FacturaCabId=235 (len={len(row_subset)}):")
        print(row_subset[['Id', 'FacturaCabId', 'nasiento', 'CodCia', 'C_TipoDoc']])
        
        # Let's run the lines loop on this subset
        for linea in sub.lineas_asiento:
            if not linea.mapeo_detalle:
                continue
            temp_df = row_subset.copy()
            cond = getattr(linea, "condicion_aplicacion", None)
            if cond:
                mask = evaluate_formula_on_df(temp_df, cond, db, 4, default=False)
                mask = pd.to_numeric(mask, errors='coerce').fillna(0).astype(bool) | (mask.astype(str).str.strip().str.upper() == 'TRUE')
                temp_df = temp_df[mask]
            
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
    from sqlalchemy import text
    main()
