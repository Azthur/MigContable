import sys
sys.path.append('c:/SistemaMigConta')
from backend.app.core.database import DestSessionLocal
from sqlalchemy import text

db = DestSessionLocal()
try:
    with db.bind.connect() as conn:
        print("=== Recent runs for ccbrgdoc (CcbGdoc) in integ_logs ===")
        query = "SELECT id, company_id, process_name, status, created_at FROM integ_logs WHERE process_name LIKE '%CcbGdoc%' ORDER BY id DESC LIMIT 5"
        res = conn.execute(text(query))
        for r in res.fetchall():
            print(dict(zip(res.keys(), r)))
finally:
    db.close()
