import sys
import os

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
            
        print("Running generator in validation collection mode...")
        rows_inserted, headers_count, validation_errors = _generate_subcategoria_cf_diariol(
            sub=sub,
            db=db,
            company_id=4,
            filters=[],
            global_lote_id="TESTLOTE",
            generate_headers=True,
            generate_details=True
        )
        print(f"Total validation errors: {len(validation_errors)}")
        for i, err in enumerate(validation_errors[:15]):
            print(f"\nError {i+1}:")
            print(f"  Field: {err.get('field')}")
            print(f"  Error: {err.get('error')}")
            print(f"  Nasiento: {err.get('nasiento')}")
            # print some of the row values if present
            row = err.get('record', {})
            print(f"  Record sample: ccodcue={row.get('ccodcue')}, npigv={row.get('npigv')}, nasiento={row.get('nasiento')}, nidlin={row.get('nidlin')}")
            
    finally:
        db.close()

if __name__ == "__main__":
    main()
