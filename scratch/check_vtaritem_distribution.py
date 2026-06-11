from backend.app.core.database import dest_engine
from sqlalchemy import text

with dest_engine.connect() as conn:
    print("--- VTARITEM RECORD DISTRIBUTION FOR COMPANY 5 ---")
    rows = conn.execute(text('SELECT "anos", "C_mes", COUNT(*) FROM vtaritem WHERE company_id = 5 GROUP BY "anos", "C_mes" ORDER BY "anos", "C_mes"')).fetchall()
    for r in rows:
        print(r)
