import sys
sys.path.append('c:/SistemaMigConta')
from backend.app.core.database import DestSessionLocal
from backend.app.models.models import MapeoSubcategoria, MapeoCategoria

db = DestSessionLocal()
try:
    subs = db.query(MapeoSubcategoria).join(MapeoCategoria).filter(
        MapeoSubcategoria.nombre.like("%024-Nota de credito%")
    ).all()
    for s in subs:
        print(f"Sub: {s.nombre} (ID: {s.id})")
        print(f"  col_origen_periodo: {s.col_origen_periodo}")
        print(f"  col_origen_mes: {s.col_origen_mes}")
        print(f"  tabla_origen: {s.tabla_origen}")
        print(f"  tabla_destino_detalle: {s.tabla_destino_detalle}")
finally:
    db.close()
