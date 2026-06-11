import urllib.request
import json

url = "http://localhost:8080/api/v1/etl/raw-table-data/1/ccbrrdoc?search=N%2FAB050000015&limit=5"
req = urllib.request.Request(url)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode("utf-8"))

print(f"Columns returned: {data.get('columns', [])}")
print(f"Total: {data.get('total')}")
print(f"Items count: {len(data.get('items', []))}")

for i, item in enumerate(data.get("items", [])):
    print(f"\n--- Item {i} ---")
    print(f"  _migration_id:       {item.get('_migration_id')}")
    print(f"  company_id:          {item.get('company_id')}")
    print(f"  NroDoc:              {item.get('NroDoc')}")
    print(f"  CodDoc:              {item.get('CodDoc')}")
    print(f"  fchdoc:              {item.get('fchdoc')}")
    print(f"  C_fechaNC:           {item.get('C_fechaNC')}")
    print(f"  C_fechaEmision:      {item.get('C_fechaEmision')}")
    print(f"  C_fechaNC_Contasis:  {item.get('C_fechaNC_Contasis')}")
    print(f"  idcontrol:           {item.get('idcontrol')}")
