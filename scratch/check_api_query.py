import os
import sys
sys.path.insert(0, os.path.abspath('backend'))
sys.path.insert(0, os.path.abspath('.'))

from app.core.database import dest_engine
from sqlalchemy import text, inspect

# Simulate what the API endpoint does
insp = inspect(dest_engine)
columns = [c['name'] for c in insp.get_columns('ccbrrdoc')]
print("=== Column order returned by API ===")
for i, col in enumerate(columns):
    print(f"  {i}: {col}")

# Simulate the search query the user does
search = "N/AB050000015"
query_str = 'SELECT * FROM "ccbrrdoc" WHERE company_id = :cid'
query_params = {"cid": 1}

search_parts = []
for idx, col in enumerate(columns):
    search_parts.append(f'CAST("{col}" AS TEXT) ILIKE :search_{idx}')
    query_params[f"search_{idx}"] = f"%{search}%"
query_str += " AND (" + " OR ".join(search_parts) + ")"

query_str += " LIMIT :limit OFFSET :offset"
query_params["limit"] = 5
query_params["offset"] = 0

with dest_engine.connect() as conn:
    result = conn.execute(text(query_str), query_params)
    rows = result.fetchall()
    keys = list(result.keys())

print(f"\n=== Found {len(rows)} rows ===")
for row in rows:
    row_dict = dict(zip(keys, row))
    # Print only the key columns
    print(f"\n--- Row ---")
    for col in ['_migration_id', 'company_id', 'NroDoc', 'CodDoc', 'fchdoc', 'C_fechaNC', 'C_fechaEmision', 'C_fechaNC_Contasis', 'idcontrol']:
        print(f"  {col}: {repr(row_dict.get(col))}")
