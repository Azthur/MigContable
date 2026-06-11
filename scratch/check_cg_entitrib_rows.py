import sys
sys.path.append('c:/SistemaMigConta')
from backend.app.core.database import dest_engine
from sqlalchemy import text

with dest_engine.connect() as conn:
    # Contar total de filas
    res = conn.execute(text("SELECT count(*) FROM cg_entitrib WHERE company_id = 1 AND subcategoria_id = 56"))
    count = res.scalar()
    print("Total rows for company 1, subcat 56:", count)
    
    # Si hay filas, mostrar las primeras 3
    if count > 0:
        res = conn.execute(text("SELECT * FROM cg_entitrib WHERE company_id = 1 AND subcategoria_id = 56 LIMIT 3"))
        keys = res.keys()
        for idx, row in enumerate(res):
            print(f"\nRow {idx}:")
            for k in keys:
                print(f"  {k}: {getattr(row, k)}")
