import sys
sys.path.append('c:/SistemaMigConta')
from backend.app.core.database import dest_engine
from sqlalchemy import inspect

insp = inspect(dest_engine)
columns = insp.get_columns('ccbrrdoc')
print("=== Columns and Types of ccbrrdoc ===")
for c in columns:
    if 'fecha' in c['name'].lower() or 'fch' in c['name'].lower() or 'emision' in c['name'].lower():
        print(f"Name: {c['name']}, Type: {c['type']}")
