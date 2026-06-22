import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ["POSTGRES_CONNECTION_STRING"] = "postgresql://postgres:postgres@localhost:5434/migconta_db"

def main():
    engine = create_engine(os.environ["POSTGRES_CONNECTION_STRING"])
    Session = sessionmaker(bind=engine)
    db = Session()

    from backend.app.models.models import MapeoSubcategoria
    from backend.app.api.endpoints.mapeo import _generate_subcategoria_cf_diariol
    
    sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == 76).first()
    
    # We will temporarily monkeypatch the insertion and just print row_dict at the end
    # Actually, let's just inspect the values of diariol_entries
    # We can fetch them since the function inserts them.
    # But wait, let's look at how they are generated.
    # We can write a custom generator loop similar to the one in mapeo.py, but importing everything.
    
    # Let's run a test by overriding the insert or just looking at the return values of _generate_subcategoria_cf_diariol
    # Wait, _generate_subcategoria_cf_diariol returns (rows_inserted, len(diario_entries), all_validation_errors)
    # It does not return the list of entries itself.
    # So let's write a python script that does the generation and prints the row_dict.
    # We'll copy the loop from mapeo.py to see exactly what happens to row_dict.
    
    import pandas as pd
    from backend.app.core.formula_parser import evaluate_formula_on_df
    from sqlalchemy import Table, MetaData
    
    metadata = MetaData()
    tabla_det_name = sub.tabla_destino_detalle or "cf_diariol"
    DetTable = Table(tabla_det_name, metadata, autoload_with=engine)
    det_cols = [c.name for c in DetTable.columns]
    
    query_str = f'SELECT * FROM "cntfacturadet" WHERE company_id = 4 AND "C_periodo" = \'2026\' AND "C_mes" = \'06\' AND "CodCia" = \'005\''
    with engine.connect() as conn:
        result = conn.execute(text := text if 'text' in locals() else __import__('sqlalchemy').text(query_str))
        rows = result.fetchall()
        columns = list(result.keys())
    df = pd.DataFrame(rows, columns=columns)
    
    # We simulate for Line 1
    linea = [l for l in sub.lineas_asiento if l.id == 344][0]
    print("Mapeo detalle:", linea.mapeo_detalle)
    
    temp_df = df.copy()
    # Apply condition
    mask = evaluate_formula_on_df(temp_df, linea.condicion_aplicacion, db, 4, default=False, db_engine=engine)
    mask_bool = pd.to_numeric(mask, errors='coerce').fillna(0).astype(bool) | (mask.astype(str).str.strip().str.upper() == 'TRUE')
    temp_df = temp_df[mask_bool]
    
    # Eval formulas
    for db_field, formula in linea.mapeo_detalle.items():
        temp_df[f"_calc_{db_field}"] = evaluate_formula_on_df(temp_df, formula, db, 4, default="", db_engine=engine)
        
    all_possible_keys = {
        "company_id", "subcategoria_id", "lote_id", "estado", "nasiento", "nidlin",
        "ndebes", "nhabers", "ndebed", "nhaberd", "ntot", "ntots", "ntotd", "idcontrol"
    }
    for l in sub.lineas_asiento:
        if l.mapeo_detalle:
            for f in l.mapeo_detalle.keys():
                if f in det_cols: all_possible_keys.add(f)
                
    row_calc = temp_df.iloc[0]
    
    row_dict = {k: None for k in all_possible_keys}
    row_dict.update({
        "company_id": 4,
        "subcategoria_id": sub.id,
        "lote_id": "TEST",
        "estado": "1",
        "nasiento": 20,
        "nidlin": 1,
        "idcontrol": str(row_calc['idcontrol']) if 'idcontrol' in row_calc else None
    })
    
    def get_det_val(field: str, default: Any = None, type_cast=str):
        col = f"_calc_{field}"
        if col not in row_calc: return default
        val = row_calc[col]
        if pd.isna(val): return default
        val_str = str(val).strip()
        if val_str == "":
            if type_cast is str and isinstance(val, str) and len(val) > 0:
                return str(val)
            if type_cast in [float, int]:
                return type_cast(0)
            return default
        if type_cast is str:
            s_val = str(val).strip()
            if s_val.endswith(".0"):
                s_val = s_val[:-2].strip()
            return s_val
        try: return type_cast(val)
        except: return default

    print("\n--- Processing fields in loop ---")
    for db_field in linea.mapeo_detalle.keys():
        if db_field not in det_cols:
            print(f"  Field {db_field} not in det_cols!")
            continue
        
        target_col = DetTable.c.get(db_field)
        type_cast = str
        is_date = False
        if target_col is not None:
            from sqlalchemy import Numeric, Integer, Float, Date
            if isinstance(target_col.type, (Numeric, Float)):
                type_cast = float
            elif isinstance(target_col.type, Integer):
                type_cast = int
            elif isinstance(target_col.type, Date):
                is_date = True
        
        val = get_det_val(db_field, None, type_cast)
        print(f"  Field: {db_field}, type_cast: {type_cast}, val: {repr(val)}")
        if val is not None:
            row_dict[db_field] = val
            
    print("\nAfter loop, row_dict:")
    print(row_dict)
    
    # Auto calculations
    if "ndebe" in row_dict or "nhaber" in row_dict:
        ndebe = float(row_dict.get("ndebe", 0.0) or 0.0)
        nhaber = float(row_dict.get("nhaber", 0.0) or 0.0)
        ntc = float(row_dict.get("ntc", 1.0) or 1.0)
        ccodmon = str(row_dict.get("ccodmon", "S") or "S")
        
        auto_vals = {
            "ndebes": ndebe if ccodmon == "S" else round(ndebe * ntc, 4),
            "nhabers": nhaber if ccodmon == "S" else round(nhaber * ntc, 4),
            "ndebed": ndebe if ccodmon == "D" else round((ndebe / ntc if ntc else 0), 4),
            "nhaberd": nhaber if ccodmon == "D" else round((nhaber / ntc if ntc else 0), 4),
            "ntot": round(ndebe + nhaber, 4)
        }
        auto_vals["ntots"] = round(auto_vals["ndebes"] + auto_vals["nhabers"], 4)
        auto_vals["ntotd"] = round(auto_vals["ndebed"] + auto_vals["nhaberd"], 4)
        
        updates = {}
        for k, v in auto_vals.items():
            user_val = row_dict.get(k)
            if k not in linea.mapeo_detalle or user_val is None:
                updates[k] = v
        row_dict.update(updates)
        
    print("\nAfter auto calculations, row_dict:")
    import pprint
    pprint.pprint({k: v for k, v in row_dict.items() if v is not None})

if __name__ == "__main__":
    main()
