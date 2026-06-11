import sys
sys.path.append('c:/SistemaMigConta')
from backend.app.core.database import DestSessionLocal, dest_engine
from sqlalchemy import text
import pandas as pd

db = DestSessionLocal()
try:
    with db.bind.connect() as conn:
        print("=== Checking specific migration IDs ===")
        ids = ["2f4f8026-5107-4748-92f9-c44cd5ba5d41", "6e677de4-7566-45cc-b8c8-7828fd145fa8"]
        for mid in ids:
            res = conn.execute(text(f'SELECT "C_car", "CodDoc", "NroDoc", "fchdoc", "C_fechaNC", "C_fechaEmision", "C_fechaNC_Contasis", "_migration_id" FROM ccbrrdoc WHERE "_migration_id" = :mid'), {"mid": mid})
            row = res.fetchone()
            if row:
                print(dict(zip(res.keys(), row)))
            else:
                print(f"Migration ID {mid} not found in DB!")
finally:
    db.close()
