import sys
sys.path.append('c:/SistemaMigConta')
from backend.app.core.database import DestSessionLocal
from backend.app.models.models import MapeoSubcategoria
from sqlalchemy import text

db = DestSessionLocal()
try:
    sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.nombre.like("%200-Cancelacion%")).first()
    if sub:
        print(f"Subcategory ID: {sub.id}")
        
        # 1. Obtener cabeceras locales
        res_h = db.execute(text("SELECT nasiento, cper, cmes, ccodori FROM cf_diario WHERE subcategoria_id = :sid AND estado = 'MIGRADO'"), {"sid": sub.id})
        h_keys = []
        for r in res_h:
            ccodori_val = str(r[3]).strip() if r[3] is not None else None
            key = (r[1], r[2], ccodori_val, r[0])
            h_keys.append((key, type(r[0])))
            
        # 2. Obtener detalles locales
        res_d = db.execute(text("SELECT nasiento, cper, cmes, ccodori FROM cf_diariol WHERE subcategoria_id = :sid AND estado = 'MIGRADO'"), {"sid": sub.id})
        d_keys = []
        for r in res_d:
            ccodori_val = str(r[3]).strip() if r[3] is not None else None
            key = (r[1], r[2], ccodori_val, r[0])
            d_keys.append((key, type(r[0])))
            
        print(f"\nTotal local headers key tuples: {len(h_keys)}")
        print(f"Total local details key tuples: {len(d_keys)}")
        
        # Mostrar las primeras 5 de cada una
        print("\nSample local headers keys:")
        for k, t in h_keys[:5]:
            print(f"  Key: {k} (nasiento type: {t})")
            
        print("\nSample local details keys:")
        for k, t in d_keys[:5]:
            print(f"  Key: {k} (nasiento type: {t})")
            
        # Comprobar coincidencias exactas
        h_set = set(k for k, t in h_keys)
        d_set = set(k for k, t in d_keys)
        
        common = h_set.intersection(d_set)
        print(f"\nUnique header keys: {len(h_set)}")
        print(f"Unique detail keys: {len(d_set)}")
        print(f"Intersection (common keys): {len(common)}")
        
        # Si la intersección es menor que unique header keys, ver cuáles no coinciden
        missing_details = h_set - d_set
        if missing_details:
            print(f"\nHeaders keys that have NO matching details keys in staging (sample of 5):")
            for k in list(missing_details)[:5]:
                print(f"  {k}")
                # Buscar en d_set si hay llaves similares pero con float/Decimal/int
                p, m, o, n = k
                similar = [dk for dk in d_set if dk[0] == p and dk[1] == m and dk[2] == o and float(dk[3]) == float(n)]
                print(f"    Similar keys in details: {similar}")
finally:
    db.close()
