import os
import sys
# Add parent dir to PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)
response = client.get("/api/v1/mapeo/origen-preview?company_id=1&limit=100&search=B050000015")
print("Status:", response.status_code)
data = response.json()
for result in data:
    table_name = result.get("table_name")
    total = result.get("total")
    items = result.get("items", [])
    print(f"\nTable: {table_name} (Total: {total}, items: {len(items)})")
    for item in items:
        # Show key columns
        print({k: item[k] for k in ["NroDoc", "Codigo", "fchdoc", "C_fechaEmision", "C_fechaNC_Contasis", "idcontrol", "_migration_id"] if k in item})
