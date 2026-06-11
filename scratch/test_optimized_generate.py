import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from backend.app.core.database import DestSessionLocal
from backend.app.models.models import MapeoSubcategoria
from backend.app.api.endpoints.mapeo import generate_to_cf_diariol
from sqlalchemy import text

def test_perf():
    db = DestSessionLocal()
    try:
        # Let's find some subcategories that have raw tables with records
        # Specifically, we want subcategories mapping to large raw tables like CcbRRdoc (ccbrrdoc)
        sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.tabla_origen.ilike('CcbRRdoc')).first()
        if not sub:
            # Fallback to any active subcategory
            sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.is_active == True).first()
            
        if not sub:
            print("No active subcategories found.")
            return

        print(f"Testing subcategory: {sub.nombre} (ID: {sub.id})")
        print(f"Source Table: {sub.tabla_origen}")
        print(f"Last Control Value: {sub.last_generated_control_value}")

        # Let's count records in the raw table first
        raw_table = sub.tabla_origen.lower().replace(" ", "_")
        try:
            cnt = db.execute(text(f'SELECT COUNT(*) FROM "{raw_table}"')).scalar()
            print(f"Raw table row count: {cnt}")
        except Exception as e:
            print(f"Could not count raw table rows: {e}")
            cnt = 0

        # Let's measure generation time
        print("\nStarting generation...")
        start_time = time.time()
        
        # Call generate_to_cf_diariol (clear_previous=True will clear non-migrated but keep migrated)
        # We can pass is_realtime=True to simulate the realtime runner
        body = {
            "company_id": 1,
            "subcategoria_id": sub.id,
            "clear_previous": False,
            "is_realtime": True
        }
        res = generate_to_cf_diariol(body, db)
        
        end_time = time.time()
        duration = end_time - start_time
        print(f"Generation completed in {duration:.4f} seconds!")
        print("Response:", res)

    except Exception as e:
        print("Error during performance test:", e)
    finally:
        db.close()

if __name__ == "__main__":
    test_perf()
