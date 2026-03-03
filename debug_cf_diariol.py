import sys
import os
import pprint
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from backend.app.core.database import DestSessionLocal
from sqlalchemy import text
import json

db = DestSessionLocal()

def check_recent_data():
    print("Checking MapeoLineaAsiento for subcategoria = 4 (ccbrgdoc)")
    from backend.app.models.models import MapeoSubcategoria
    sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == 4).first()
    for l in sub.lineas_asiento:
        print(f"Linea {l.orden}:")
        print(json.dumps(l.mapeo_detalle, indent=2))
        break # just check the first line

    print("\nChecking recent records in cf_diariol (Subcat 4)")
    result = db.execute(text("""
        SELECT * FROM cf_diariol 
        WHERE subcategoria_id = 4 
        ORDER BY nasiento DESC, nidlin ASC 
        LIMIT 5
    """)).mappings().all()
    
    for row in result:
        print(f"--- nasiento: {row['nasiento']}, nidlin: {row['nidlin']} ---")
        print(f"ndebe: {row['ndebe']}  nhaber: {row['nhaber']}")
        print(f"ndebes: {row['ndebes']}  nhabers: {row['nhabers']}")
        print(f"ndebed: {row['ndebed']}  nhaberd: {row['nhaberd']}")
        print(f"ntot: {row['ntot']}  ntots: {row['ntots']}  ntotd: {row['ntotd']}")

if __name__ == "__main__":
    check_recent_data()
