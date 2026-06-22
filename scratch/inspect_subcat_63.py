import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.core.database import DestSessionLocal
from backend.app.models.models import MapeoSubcategoria, MapeoLineaAsiento

db = DestSessionLocal()
sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == 63).first()
if not sub:
    print("Subcategory 63 not found")
else:
    print(f"Subcategory ID: {sub.id}")
    print(f"Name: {sub.nombre}")
    print(f"Table origen: {sub.tabla_origen}")
    print(f"Generate headers: {sub.generate_headers}")
    print(f"Generate details: {sub.generate_details}")
    print(f"Filter rules: {sub.filter_rules}")
    print(f"Clave asiento: {sub.clave_asiento}")
    print(f"Col Destino Nasiento: {sub.col_destino_nasiento}")
    print(f"Col Destino Nidlin: {sub.col_destino_nidlin}")
    
    print("\nLineas de Asiento:")
    lineas = db.query(MapeoLineaAsiento).filter(MapeoLineaAsiento.subcategoria_id == 63).all()
    for l in lineas:
        print(f"  Line ID: {l.id}, Orden: {l.orden}, Nombre: {l.nombre_linea}")
        print(f"  Condicion: {l.condicion_aplicacion}")
        print(f"  Mapeo Detalle: {l.mapeo_detalle}")
        print("-" * 50)
db.close()
