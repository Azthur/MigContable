import os
import sys
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ["POSTGRES_CONNECTION_STRING"] = "postgresql://postgres:postgres@localhost:5434/migconta_db"

def main():
    engine = create_engine(os.environ["POSTGRES_CONNECTION_STRING"])
    Session = sessionmaker(bind=engine)
    db = Session()

    from backend.app.models.models import MapeoSubcategoria, MapeoLineaAsiento
    from backend.app.core.formula_parser import evaluate_formula_on_df
    
    sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == 76).first()
    company_id = 4
    
    print(f"Subcategory: {sub.nombre}")
    print(f"Filter rules: {sub.filter_rules}")
    
    # Let's query the source rows
    query_str = f'SELECT * FROM "cntfacturadet" WHERE company_id = {company_id} AND "C_periodo" = \'2026\' AND "C_mes" = \'06\' AND "CodCia" = \'005\''
    with engine.connect() as conn:
        result = conn.execute(text(query_str))
        rows = result.fetchall()
        columns = list(result.keys())
    
    df = pd.DataFrame(rows, columns=columns)
    print(f"\nFound {len(df)} source rows in DataFrame.")
    print("Columns:", list(df.columns))
    
    # Retrieve active lines
    lineas = db.query(MapeoLineaAsiento).filter(
        MapeoLineaAsiento.subcategoria_id == sub.id,
        MapeoLineaAsiento.is_active == True
    ).order_by(MapeoLineaAsiento.orden).all()
    
    print(f"\nActive lines count: {len(lineas)}")
    
    for idx, linea in enumerate(lineas):
        print(f"\n--- Line {idx+1}: ID={linea.id}, Name='{linea.nombre_linea}', Nivel={linea.nivel} ---")
        print(f"  Condition formula: {repr(linea.condicion_aplicacion)}")
        
        # Test condition evaluation
        temp_df = df.copy()
        if linea.condicion_aplicacion:
            try:
                mask = evaluate_formula_on_df(temp_df, linea.condicion_aplicacion, db, company_id, default=False, db_engine=engine)
                print(f"  Parsed mask (first 5 elements): {list(mask.head())}")
                mask_bool = pd.to_numeric(mask, errors='coerce').fillna(0).astype(bool) | (mask.astype(str).str.strip().str.upper() == 'TRUE')
                print(f"  Mask boolean (first 5 elements): {list(mask_bool.head())}")
                temp_df = temp_df[mask_bool]
                print(f"  Filtered rows count: {len(temp_df)}")
            except Exception as e:
                print(f"  Error evaluating condition: {e}")
                continue
        else:
            print(f"  No condition formula.")
            
        if temp_df.empty:
            print("  DataFrame is empty for this line. Skipping.")
            continue
            
        # Evaluate details
        for db_field, formula in linea.mapeo_detalle.items():
            calc_val = evaluate_formula_on_df(temp_df, formula, db, company_id, default="", db_engine=engine)
            temp_df[f"_calc_{db_field}"] = calc_val
            
        # If Nivel is CABECERA, drop duplicates
        if linea.nivel == "CABECERA":
            temp_df = temp_df.drop_duplicates(subset=['idcontrol'])
            print(f"  Dropped duplicates (Nivel=CABECERA). Remaining rows: {len(temp_df)}")
            
        # Print first row's calculated values for key fields
        for _, row_calc in temp_df.iterrows():
            print(f"  Row idcontrol={row_calc['idcontrol']}:")
            # Print mapped fields
            for db_field in linea.mapeo_detalle.keys():
                col = f"_calc_{db_field}"
                val = row_calc.get(col)
                print(f"    {db_field} formula={linea.mapeo_detalle[db_field]} -> value={repr(val)}")
                
            # Simulate mapping/auto calculations
            ndebe = 0.0
            if f"_calc_ndebe" in row_calc:
                try: ndebe = float(row_calc["_calc_ndebe"])
                except: pass
            nhaber = 0.0
            if f"_calc_nhaber" in row_calc:
                try: nhaber = float(row_calc["_calc_nhaber"])
                except: pass
            
            print(f"    Simulated inputs: ndebe={ndebe}, nhaber={nhaber}")
            
            # Let's check how ccodmon/ntc affects it
            ccodmon = "S"
            if "_calc_ccodmon" in row_calc:
                ccodmon = str(row_calc["_calc_ccodmon"])
            ntc = 1.0
            if "_calc_ntc" in row_calc:
                try: ntc = float(row_calc["_calc_ntc"])
                except: pass
                
            ndebes = ndebe if ccodmon == "S" else round(ndebe * ntc, 4)
            nhabers = nhaber if ccodmon == "S" else round(nhaber * ntc, 4)
            print(f"    Simulated calculations: ndebes={ndebes}, nhabers={nhabers}")

if __name__ == "__main__":
    main()
