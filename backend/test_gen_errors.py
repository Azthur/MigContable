import sys
import os
sys.path.append(r"c:\SistemaMigConta")

from backend.app.core.database import DestSessionLocal, source_engine
from backend.app.models.models import MapeoSubcategoria
from backend.app.api.endpoints.mapeo import _generate_subcategoria_cf_diariol

db = DestSessionLocal()
subs = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.is_active == True).all()

total_errors = []
print(f"Simulando Generación para {len(subs)} subcategorías...")

for sub in subs:
    try:
        # Usamos company_id=1
        res = _generate_subcategoria_cf_diariol(sub, db, 1)
        errs = res[2] if len(res) > 2 else []
        total_errors.extend(errs)
    except Exception as e:
        print(f"Error procesando {sub.nombre}: {e}")

print("\n--- RESULTADO TOTAL ---")
print("Total Errores:", len(total_errors))

if total_errors:
    fields_count = {}
    for e in total_errors:
        f = e.get("field", "unknown")
        fields_count[f] = fields_count.get(f, 0) + 1

    print("\nResumen de Errores por Campo:")
    for f, count in fields_count.items():
        print(f"- {f}: {count} errores")

    print("\nDetalle de ejemplos:")
    for e in total_errors[:5]:
        print(f"Subcat: {e.get('subcategoria_id')}, Campo: {e['field']}, Error: {e['error']}, Asiento: {e.get('nasiento')}")
else:
    print("No se encontraron errores en la simulación de memoria.")

db.close()
