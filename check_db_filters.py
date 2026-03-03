import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.core.database import DestSessionLocal

db = DestSessionLocal()
try:
    res = db.execute(text("SELECT id, nombre, filter_rules FROM mapeo_subcategorias WHERE filter_rules IS NOT NULL")).fetchall()
    for row in res:
        print(f"Subcategoria {row[0]} ({row[1]}): {row[2]}")
finally:
    db.close()
