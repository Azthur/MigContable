import sys
import os

# Set up environment
sys.path.insert(0, r"C:\SistemaMigConta")
os.environ["PYTHONPATH"] = r"C:\SistemaMigConta"

from backend.app.core.database import DestSessionLocal
from backend.app.api.endpoints.mapeo import generate_to_cf_diariol

db = DestSessionLocal()
try:
    print("Testing generate_to_cf_diariol internally...")
    res = generate_to_cf_diariol(
        body={"subcategoria_id": 4, "periodo": "2026", "mes": "01"},
        db=db
    )
    print("SUCCESS:", res)
except Exception as e:
    import traceback
    print("CRASHED!")
    traceback.print_exc()
finally:
    db.close()
