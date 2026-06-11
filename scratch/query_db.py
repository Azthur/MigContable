import sys
sys.path.append('c:/SistemaMigConta')
from backend.app.core.database import DestSessionLocal
from sqlalchemy import text
db = DestSessionLocal()
with db.bind.connect() as conn:
    print("--- ccbrrdoc FCHDOC not null ---")
    res = conn.execute(text("SELECT fchdoc, \"C_fechaEmision\", \"C_car\" FROM ccbrrdoc WHERE fchdoc IS NOT NULL LIMIT 5"))
    for row in res.fetchall():
        print(dict(zip(res.keys(), row)))
