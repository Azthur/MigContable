import sys
import os
import pandas as pd
from sqlalchemy import create_engine

# Add project root to path
sys.path.append("c:\\SistemaMigConta")

os.environ["POSTGRES_CONNECTION_STRING"] = "postgresql://postgres:postgres@localhost:5434/migconta_db"

from backend.app.core.database import DestSessionLocal
from backend.app.models.models import MapeoSubcategoria
from backend.app.api.endpoints.mapeo import _generate_subcategoria_cf_diariol

def main():
    db = DestSessionLocal()
    try:
        sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == 63).first()
        if not sub:
            print("Subcategory 63 not found!")
            return
            
        print("Calling _generate_subcategoria_cf_diariol...")
        # Clear previous first to simulate fresh run
        # Run generator
        rows_inserted, headers_count, validation_errors = _generate_subcategoria_cf_diariol(
            sub=sub,
            db=db,
            company_id=4,
            filters=[
                {"column": "C_periodo", "operator": "=", "value": "2026"},
                {"column": "C_mes", "operator": "=", "value": "06"}
            ],
            global_lote_id="TESTLOTE",
            generate_headers=True,
            generate_details=True
        )
        print("Rows inserted (details):", rows_inserted)
        print("Headers count:", headers_count)
        print("Validation errors:", len(validation_errors))
        for err in validation_errors:
            print("  Err:", err.get("error"))
            
    finally:
        db.close()

if __name__ == "__main__":
    main()
