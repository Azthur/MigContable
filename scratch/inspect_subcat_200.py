import sys
sys.path.append('c:/SistemaMigConta')
from backend.app.core.database import DestSessionLocal
from backend.app.models.models import MapeoSubcategoria

db = DestSessionLocal()
try:
    sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.nombre.like("%200-Cancelacion%")).first()
    if sub:
        print(f"Subcategoria 200 Configuration:")
        print(f"  Nombre: {sub.nombre}")
        print(f"  Codigo Origen (ccodori): '{sub.codigo_origen}'")
        print(f"  Tabla Origen: '{sub.tabla_origen}'")
        print(f"  Tabla Destino Cabecera: '{sub.tabla_destino_cabecera}'")
        print(f"  Tabla Destino Detalle: '{sub.tabla_destino_detalle}'")
        print(f"  Generate Headers: {sub.generate_headers}")
        print(f"  Generate Details: {sub.generate_details}")
    else:
        print("Subcategory 200 not found!")
finally:
    db.close()
