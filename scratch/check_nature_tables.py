from backend.app.core.database import dest_engine
from sqlalchemy import text

with dest_engine.connect() as conn:
    print("--- SUBCATEGORIES FOR COMPANY 5 (YELAVE NATURE) ---")
    subs = conn.execute(text("""
        SELECT ms.id, ms.nombre, ms.tabla_origen, ms.clave_asiento, ms.control_column_origen, ms.last_generated_control_value
        FROM mapeo_subcategorias ms
        JOIN mapeo_categorias mc ON ms.categoria_id = mc.id
        WHERE mc.company_id = 5
    """)).fetchall()
    for s in subs:
        print(s)
        
        # Check intermediate table record count and date ranges if present
        table_name = s[2]
        if table_name:
            try:
                t_count = conn.execute(text(f'SELECT COUNT(*) FROM "{table_name.lower()}" WHERE company_id = 5')).scalar()
                print(f"Table '{table_name}' count for company 5: {t_count}")
                
                # Check date columns or recent records
                cols_res = conn.execute(text(f"SELECT * FROM \"{table_name.lower()}\" WHERE company_id = 5 LIMIT 3"))
                cols = list(cols_res.keys())
                rows = cols_res.fetchall()
                print(f"Columns: {cols}")
                for r in rows:
                    print(r)
            except Exception as e:
                print(f"Error checking table '{table_name}': {e}")
