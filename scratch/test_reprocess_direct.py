from backend.app.core.database import DestSessionLocal
from backend.app.api.endpoints.etl import reextract_reprocess

db = DestSessionLocal()
try:
    body = {
        "company_id": 4,
        "subcategoria_id": 63
    }
    res = reextract_reprocess(body, db)
    print("Reprocess SUCCESS:", res)
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    db.close()
