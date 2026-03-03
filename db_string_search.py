import sys
sys.path.insert(0, r"c:\SistemaMigConta")
from backend.app.core.database import dest_engine
from sqlalchemy import text

query = "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
with dest_engine.connect() as conn:
    tables = [r[0] for r in conn.execute(text(query)).fetchall()]

found = False
for t in tables:
    try:
        with dest_engine.connect() as conn:
            cols_query = text(f"SELECT column_name FROM information_schema.columns WHERE table_name='{t}' AND data_type IN ('character varying', 'text')")
            text_cols = [r[0] for r in conn.execute(cols_query).fetchall()]
            
            for col in text_cols:
                search_query = text(f'SELECT "{col}" FROM "{t}" WHERE "{col}" LIKE \'%SI.CONJUNTO%\' LIMIT 10')
                res = conn.execute(search_query).fetchall()
                if res:
                    print(f"FOUND IN {t}.{col}:")
                    for r in res:
                        print(f"  {r[0]}")
                    found = True
    except Exception as e:
        pass

if not found:
    print("NO STRING LIKE 'SI.CONJUNTO' FOUND IN ANY DESTINATION TABLE TEXT COLUMNS.")
