import sys
import os
import pprint
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from backend.app.core.database import DestSessionLocal
from sqlalchemy import text
import json

db = DestSessionLocal()

def inspect_user_mappings():
    print("Fetching active mapped lines for company records...")
    from backend.app.models.models import MapeoSubcategoria
    # Get all subcategories currently mapped
    subs = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.tabla_origen != None).all()
    for sub in subs:
        if not sub.lineas_asiento: continue
        print(f"\n--- Subcategoria: {sub.id} - {sub.nombre} ({sub.tabla_origen}) ---")
        for l in sub.lineas_asiento:
            if not l.is_active: continue
            print(f"  Line {l.orden}: condicion -> {l.condicion_aplicacion}")
            keys_to_check = ["ndebe", "nhaber", "ndebes", "nhabers", "ndebed", "nhaberd", "ntot", "ntots", "ntotd"]
            condensed = {k: l.mapeo_detalle.get(k) for k in keys_to_check}
            print(f"  Line {l.orden} math formulas: {condensed}")

if __name__ == "__main__":
    inspect_user_mappings()
