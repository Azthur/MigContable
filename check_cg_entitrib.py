from backend.app.core.database import DestSessionLocal
from sqlalchemy import text

db = DestSessionLocal()
result = db.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'cg_entitrib' ORDER BY ordinal_position")).fetchall()
print("=== ESTRUCTURA TABLA cg_entitrib ===")
for r in result:
    print(f'{r[0]}: {r[1]}')
db.close()
