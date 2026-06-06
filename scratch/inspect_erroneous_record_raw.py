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
            
        # Reset subcategory control value first
        db.execute(text("UPDATE mapeo_subcategorias SET last_generated_control_value = NULL, asiento_inicial = 1 WHERE id = 63"))
        db.commit()
        
        print("Running generator...")
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
        for idx, err in enumerate(validation_errors):
            print(f"\n--- Error {idx+1} ---")
            print(f"Field: {err.get('field')}")
            print(f"Error: {err.get('error')}")
            record = err.get('record', {})
            print("Record keys and values:")
            for k, v in record.items():
                print(f"  {k}: {repr(v)}")
            if idx >= 1:
                break
                
    finally:
        db.close()

if __name__ == "__main__":
    from sqlalchemy import text
    main()
