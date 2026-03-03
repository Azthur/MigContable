import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from backend.app.core.database import DestSessionLocal
from backend.app.models.models import MapeoSubcategoria
from backend.app.api.endpoints.mapeo import _generate_subcategoria_cf_diariol

db = DestSessionLocal()

def test_filters():
    # Use subcategory ID 4 (Compras - ccbrgdoc) or 5 (Ventas - vtaritem)
    sub_id = 4
    sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == sub_id).first()
    
    if not sub:
        print(f"Subcategory {sub_id} not found.")
        return
        
    print(f"Testing subcategory: {sub.nombre} (Table: {sub.tabla_origen})")
    
    # 1. Test without filters
    sub.filter_rules = []
    db.commit()
    print("\n--- Testing Without Filters ---")
    gen, asis = _generate_subcategoria_cf_diariol(
        sub=sub,
        db=db,
        company_id=sub.categoria.company_id,
        filters=[],
        global_lote_id="TEST-NOFILT"
    )
    print(f"Generated {gen} lines across {asis} seats.")

    # 2. Test with some filters (e.g. ano = 2026 if 'anos' column exists)
    # We simulate a UI filter rule
    sub.filter_rules = [
        {"column": "anos", "operator": "=", "value": "2026"},
        {"column": "C_mes", "operator": ">=", "value": "01"}
    ]
    db.commit()
    print("\n--- Testing With Filters (anos=2026, C_mes>=01) ---")
    gen, asis = _generate_subcategoria_cf_diariol(
        sub=sub,
        db=db,
        company_id=sub.categoria.company_id,
        filters=[],
        global_lote_id="TEST-FILT"
    )
    print(f"Generated {gen} lines across {asis} seats.")
    
    # Clean up
    sub.filter_rules = []
    db.commit()
    print("Test complete.")

if __name__ == "__main__":
    test_filters()
