import os
from sqlalchemy import create_engine, text

os.environ["POSTGRES_CONNECTION_STRING"] = "postgresql://postgres:postgres@localhost:5434/migconta_db"

def main():
    engine = create_engine(os.environ["POSTGRES_CONNECTION_STRING"])
    with engine.connect() as conn:
        print("--- Subcategory 76 Mapping ---")
        res_sub = conn.execute(text("SELECT id, nombre, tabla_origen, clave_asiento, filter_rules, generate_headers, generate_details FROM mapeo_subcategorias WHERE id = 76")).mappings().first()
        if res_sub:
            print(dict(res_sub))
        else:
            print("Subcategory 76 not found!")
            return
        
        # Check mapping lines
        res_lines = conn.execute(text("SELECT id, orden, nombre_linea, condicion_aplicacion, mapeo_detalle, nivel FROM mapeo_lineas_asiento WHERE subcategoria_id = 76 ORDER BY orden")).mappings().all()
        print(f"\nFound {len(res_lines)} mapping lines:")
        for idx, line in enumerate(res_lines):
            print(f"\nLine {idx+1}: ID={line['id']}, Name='{line['nombre_linea']}', Nivel={line['nivel']}, Orden={line['orden']}")
            print(f"  Condition: {line['condicion_aplicacion']}")
            print(f"  Mapping Detail: {line['mapeo_detalle']}")
            
        # Let's inspect the source data in cntfacturadet for this period
        # The filter is c_periodo = 2026, c_mes = 06, CodCia = 005
        # Wait, what columns are in cntfacturadet? Let's check first 5 rows or count
        print("\n--- Source Table Structure/Rows in cntfacturadet ---")
        count_res = conn.execute(text("SELECT COUNT(*) FROM cntfacturadet")).scalar()
        print(f"Total rows in cntfacturadet: {count_res}")
        
        # Query with filters
        # Note: sometimes columns might be C_periodo, C_mes, CodCia. Let's see if we can do a SELECT with those filters.
        try:
            res_data = conn.execute(text("""
                SELECT * FROM cntfacturadet 
                WHERE "C_periodo" = '2026' AND "C_mes" = '06' AND "CodCia" = '005'
            """)).mappings().all()
            print(f"Filtered source rows count: {len(res_data)}")
            for idx, r in enumerate(res_data):
                print(f"\nRow {idx+1}:")
                # print keys/values
                for k, v in r.items():
                    if v is not None and v != '':
                        print(f"  {k}: {v}")
        except Exception as e:
            print("Error querying cntfacturadet with filters:", e)
            # Let's get columns of cntfacturadet
            cols = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'cntfacturadet'")).scalars().all()
            print("Columns in cntfacturadet:", cols)

if __name__ == "__main__":
    main()
