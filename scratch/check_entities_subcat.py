import sys
sys.path.append('c:/SistemaMigConta')
from backend.app.core.database import DestSessionLocal
from backend.app.models.models import MapeoSubcategoria

db = DestSessionLocal()
try:
    sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.nombre.like("%Entidades%")).first()
    if sub:
        print("Subcategory ID:", sub.id)
        print("Name:", sub.nombre)
        print("Tabla Origen:", sub.tabla_origen)
        print("Tabla Destino Cabecera:", sub.tabla_destino_cabecera)
        print("Tabla Destino Detalle:", sub.tabla_destino_detalle)
        print("Col Destino Nasiento:", sub.col_destino_nasiento)
        print("Col Destino Nidlin:", sub.col_destino_nidlin)
        print("Col Origen Periodo:", getattr(sub, "col_origen_periodo", None))
        print("Col Origen Mes:", getattr(sub, "col_origen_mes", None))
        print("Asiento Inicial:", getattr(sub, "asiento_inicial", None))
        print("Last Generated Control Value:", sub.last_generated_control_value)
    else:
        print("No subcategory containing 'Entidades' found.")
finally:
    db.close()
