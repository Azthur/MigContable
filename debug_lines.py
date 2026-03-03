import sys
import os
import pprint
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from backend.app.core.database import DestSessionLocal
from backend.app.models.models import MapeoSubcategoria
from backend.app.api.endpoints.mapeo import _generate_subcategoria_cf_diariol

db = DestSessionLocal()

def inspect_lines():
    sub_id = 4 # ccbrgdoc
    sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == sub_id).first()
    
    if not sub:
        print("Subcategory not found.")
        return

    # To see what is being mapped to MapeoLineaAsiento
    for linea in sub.lineas_asiento:
        print(f"Line {linea.orden}:")
        print(f" - mapped details keys: {list(linea.mapeo_detalle.keys()) if linea.mapeo_detalle else None}")
        
    print("\n--- Generating some records to see output data ---")
    sub.filter_rules = [
        {"column": "anos", "operator": "=", "value": "2026"}
    ]
    db.commit()

    import mock
    with mock.patch('backend.app.api.endpoints.mapeo.db.execute') as mock_exec:
        # We will patch the db.execute temporarily to catch the diariol_entries
        from sqlalchemy import text
        original_execute = db.execute
        
        # We can just monkey patch the function or insert a print inside it
        pass

inspect_lines()
