import sys
sys.path.append('c:/SistemaMigConta')
from backend.app.core.database import DestSessionLocal
from backend.app.models.models import MapeoSubcategoria
from sqlalchemy import text

db = DestSessionLocal()
try:
    sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.nombre.like("%200-Cancelacion%")).first()
    if sub:
        print(f"Subcategory: {sub.nombre} (ID: {sub.id})")
        # 1. Cabeceras locales
        res_h = db.execute(text("SELECT nasiento, cper, cmes, ccodori, estado FROM cf_diario WHERE subcategoria_id = :sid LIMIT 3"), {"sid": sub.id})
        print("\nStaging cf_diario (headers) sample:")
        for r in res_h:
            print(f"  nasiento: {r[0]} ({type(r[0])}) | cper: {r[1]} ({type(r[1])}) | cmes: {r[2]} ({type(r[2])}) | ccodori: {r[3]} ({type(r[3])}) | estado: {r[4]}")
            
        # 2. Detalles locales
        res_d = db.execute(text("SELECT nasiento, nidlin, cper, cmes, ccodori, estado FROM cf_diariol WHERE subcategoria_id = :sid LIMIT 3"), {"sid": sub.id})
        print("\nStaging cf_diariol (details) sample:")
        for r in res_d:
            print(f"  nasiento: {r[0]} ({type(r[0])}) | nidlin: {r[1]} ({type(r[1])}) | cper: {r[2]} ({type(r[2])}) | cmes: {r[3]} ({type(r[3])}) | ccodori: {r[4]} ({type(r[4])}) | estado: {r[5]}")
    else:
        print("Subcategory not found!")
finally:
    db.close()
