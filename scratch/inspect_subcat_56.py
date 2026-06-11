import sys
sys.path.append('c:/SistemaMigConta')
from backend.app.core.database import DestSessionLocal
from backend.app.models.models import MapeoLineaAsiento

db = DestSessionLocal()
try:
    lines = db.query(MapeoLineaAsiento).filter(MapeoLineaAsiento.subcategoria_id == 56).all()
    for idx, l in enumerate(lines):
        print(f"\n--- Line {idx} ---")
        for k, v in vars(l).items():
            if not k.startswith('_'):
                print(f"  {k}: {v}")
finally:
    db.close()
