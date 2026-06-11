import sys
sys.path.append('c:/SistemaMigConta')
from backend.app.core.database import DestSessionLocal
from backend.app.models.models import TableSelection
from sqlalchemy import text

db = DestSessionLocal()
try:
    # Find selection
    sel = db.query(TableSelection).filter(TableSelection.table_name.ilike('%gdoc%')).all()
    print("=== Table Selections matching gdoc ===")
    for s in sel:
        print(f"ID: {s.id}, Name: {s.table_name}, Selected: {s.is_selected}, Company ID: {s.company_id}")
        
        # Search for runs in integ_logs
        with db.bind.connect() as conn:
            query = "SELECT id, company_id, process_name, status, created_at FROM integ_logs WHERE process_name LIKE :proc ORDER BY id DESC LIMIT 3"
            res = conn.execute(text(query), {"proc": f"%{s.table_name}%"})
            for r in res.fetchall():
                print("  Run:", dict(zip(res.keys(), r)))
finally:
    db.close()
