import sys
sys.path.append('c:/SistemaMigConta')
from backend.app.core.database import DestSessionLocal
from sqlalchemy import text

db = DestSessionLocal()
with db.bind.connect() as conn:
    res = conn.execute(text("""
        SELECT new_column_name, priority, condition_value 
        FROM computed_column_rules 
        WHERE table_selection_id = 56 
        AND new_column_name IN ('fchdoc', 'C_fechaEmision', 'C_fechaNC_Contasis', 'C_fechaNC', 'coddoc')
        ORDER BY priority ASC
    """))
    for row in res.fetchall():
        print(row)
