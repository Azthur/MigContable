import sys
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)
sys.path.insert(0, r"c:\SistemaMigConta")
from backend.app.core.database import dest_engine
from sqlalchemy import text

query = "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
with dest_engine.connect() as conn:
    tables = [r[0] for r in conn.execute(text(query)).fetchall()]

for t in tables:
    if t.startswith('cf_') or t == 'alembic_version': continue
    try:
        with dest_engine.connect() as conn:
            cols = [c[0] for c in conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name='{t}'")).fetchall()]
            if '_Seriedoc' in cols:
                print(f"Table {t} has _Seriedoc")
                res = conn.execute(text(f'SELECT "_Seriedoc" FROM "{t}" LIMIT 5')).fetchall()
                for i, r in enumerate(res):
                    print(f"  Row {i}: {r[0]}")
    except Exception as e:
        pass
