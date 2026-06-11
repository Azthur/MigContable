import sys
sys.path.append('c:/SistemaMigConta')
from backend.app.core.database import DestSessionLocal
from backend.app.models.models import MapeoSubcategoria

db = DestSessionLocal()
try:
    subs = db.query(MapeoSubcategoria).all()
    for s in subs:
        print(f"ID: {s.id}, Name: {s.nombre}, DestDetalle: {s.tabla_destino_detalle}, ColPeriodo: {s.col_origen_periodo}, ColMes: {s.col_origen_mes}")
finally:
    db.close()
