import sys
sys.path.append("c:\\SistemaMigConta")
from backend.app.core.database import DestSessionLocal
from backend.app.models.models import MapeoCategoria, MapeoSubcategoria, MapeoLineaAsiento
from backend.app.api.endpoints.mapeo import _generate_subcategoria_cf_diariol
import json
import uuid

db = DestSessionLocal()
sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.tabla_origen == 'vtaritem').first()
if sub:
    print(f"Found Sub: {sub.id} - {sub.nombre}")
    try:
        gen, asis = _generate_subcategoria_cf_diariol(sub, db, sub.categoria.company_id, "2026", "01", [], str(uuid.uuid4())[:8])
        print(f"Result: {gen} generated, {asis} asientos")
    except Exception as e:
        print("Exception during generation:", e)
else:
    print("Subcategoria with table 'vtaritem' not found")
