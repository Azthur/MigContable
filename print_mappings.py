import sys
sys.path.append("c:\\SistemaMigConta")
from backend.app.core.database import DestSessionLocal
from backend.app.models.models import MapeoCategoria, MapeoSubcategoria, MapeoLineaAsiento
import json

db = DestSessionLocal()
cats = db.query(MapeoCategoria).all()
for cat in cats:
    print(f"Cat: {cat.id} - {cat.nombre}")
    for sub in cat.subcategorias:
        print(f"  Sub: {sub.id} - {sub.nombre} (Tabla: {sub.tabla_origen})")
        print(f"    Cabecera: {json.dumps(sub.mapeo_cabecera)}")
        for linea in sub.lineas_asiento:
            print(f"      Linea {linea.orden}: {linea.nombre_linea}")
            print(f"        Detalle: {json.dumps(linea.mapeo_detalle)}")
