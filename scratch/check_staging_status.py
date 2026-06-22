import os
import sys
sys.path.append(os.path.abspath('.'))
sys.path.append(os.path.abspath('backend'))
from backend.app.core.database import dest_engine
from sqlalchemy import text

conn = dest_engine.connect()
print("--- cf_diario staging for (2026, 04, 200, 1386) ---")
r1 = conn.execute(text("select * from cf_diario where company_id=1 and subcategoria_id=43 and cper='2026' and cmes='04' and ccodori='200' and nasiento=1386")).fetchall()
for row in r1:
    print(dict(row._mapping))

print("\n--- cf_diariol staging for (2026, 04, 200, 1386) ---")
r2 = conn.execute(text("select id, cper, cmes, nasiento, nidlin, estado from cf_diariol where company_id=1 and subcategoria_id=43 and cper='2026' and cmes='04' and ccodori='200' and nasiento=1386")).fetchall()
for row in r2:
    print(dict(row._mapping))
