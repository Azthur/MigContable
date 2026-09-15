"""
Script de verificacion (SOLO LECTURA) de consistencia de migracion:
  Migconta (staging) vs Contasis (destino final).
Uso: python verify_migration.py <company_id>
"""
import sys
import logging

logging.disable(logging.CRITICAL)

from sqlalchemy import text
from backend.app.core.database import DestSessionLocal, dest_engine
from backend.app.models.models import FinalDestConnection
from backend.app.services.connection_manager import ConnectionManager

company_id = int(sys.argv[1]) if len(sys.argv) > 1 else 5

db = DestSessionLocal()

print(f"===== VERIFICACION EMPRESA {company_id} =====\n")

# ── 1. Conteos por estado en staging ──
print("--- 1. STAGING (migconta_db) cf_diariol: conteo por estado/periodo/mes ---")
rows = db.execute(text("""
    SELECT cper, cmes, estado, COUNT(*) AS lineas, COUNT(DISTINCT nasiento) AS asientos
    FROM cf_diariol
    WHERE company_id = :cid
    GROUP BY cper, cmes, estado
    ORDER BY cper, cmes, estado
"""), {"cid": company_id}).fetchall()
for r in rows:
    print(f"  {r.cper}-{r.cmes} | {r.estado:12s} | lineas: {r.lineas:7d} | asientos: {r.asientos}")

print("\n--- 1b. STAGING cf_diario (cabeceras): conteo por estado ---")
rows = db.execute(text("""
    SELECT cper, cmes, estado, COUNT(*) AS cabeceras
    FROM cf_diario
    WHERE company_id = :cid
    GROUP BY cper, cmes, estado
    ORDER BY cper, cmes, estado
"""), {"cid": company_id}).fetchall()
for r in rows:
    print(f"  {r.cper}-{r.cmes} | {r.estado:12s} | cabeceras: {r.cabeceras}")

# ── 2. Duplicados internos en staging (misma llave de asiento+linea repetida) ──
print("\n--- 2. DUPLICADOS INTERNOS en staging (misma llave cper,cmes,ccodori,nasiento,nidlin) ---")
rows = db.execute(text("""
    SELECT cper, cmes, ccodori, nasiento, nidlin, COUNT(*) AS veces
    FROM cf_diariol
    WHERE company_id = :cid
    GROUP BY cper, cmes, ccodori, nasiento, nidlin
    HAVING COUNT(*) > 1
    ORDER BY veces DESC
    LIMIT 20
"""), {"cid": company_id}).fetchall()
if rows:
    for r in rows:
        print(f"  {r.cper}-{r.cmes}-{r.ccodori}-{r.nasiento} lin {r.nidlin}: {r.veces} veces")
    total_dup = db.execute(text("""
        SELECT COUNT(*) FROM (
            SELECT 1 FROM cf_diariol WHERE company_id = :cid
            GROUP BY cper, cmes, ccodori, nasiento, nidlin HAVING COUNT(*) > 1
        ) t
    """), {"cid": company_id}).scalar()
    print(f"  TOTAL llaves duplicadas internamente: {total_dup}")
else:
    print("  Sin duplicados internos.")

# ── 3. Conexion a Contasis ──
final_conn = db.query(FinalDestConnection).filter(
    FinalDestConnection.company_id == company_id,
    FinalDestConnection.is_active == True
).first()

if not final_conn:
    print("\nNo hay conexion Contasis configurada para esta empresa. Fin.")
    db.close()
    sys.exit(0)

print(f"\n--- 3. CONTASIS: {final_conn.host}:{final_conn.port}/{final_conn.database_name} ---")
final_engine = ConnectionManager.get_dest_engine({
    "host": final_conn.host, "port": final_conn.port,
    "database_name": final_conn.database_name,
    "username": final_conn.username, "password": final_conn.password
})

with final_engine.connect() as fdb:
    # Llaves de asiento existentes en Contasis (cabeceras)
    contasis_keys = set()
    for r in fdb.execute(text("SELECT cper, cmes, TRIM(ccodori), nasiento FROM cf_diario")):
        contasis_keys.add((str(r[0]), str(r[1]), str(r[2]), int(r[3]) if r[3] is not None else None))
    print(f"  Asientos (cabeceras) en Contasis: {len(contasis_keys)}")

    contasis_det = fdb.execute(text("SELECT COUNT(*) FROM cf_diariol")).scalar()
    print(f"  Lineas de detalle en Contasis: {contasis_det}")

# ── 4. Asientos PENDIENTE en staging que YA EXISTEN en Contasis (causa del UniqueViolation) ──
print("\n--- 4. Asientos PENDIENTE en staging que YA existen en Contasis ---")
pend = db.execute(text("""
    SELECT DISTINCT cper, cmes, TRIM(ccodori) AS ccodori, nasiento
    FROM cf_diariol
    WHERE company_id = :cid AND estado = 'PENDIENTE'
"""), {"cid": company_id}).fetchall()
pend_keys = [(str(r.cper), str(r.cmes), str(r.ccodori), int(r.nasiento) if r.nasiento is not None else None) for r in pend]
ya_existen = [k for k in pend_keys if k in contasis_keys]
no_existen = [k for k in pend_keys if k not in contasis_keys]
print(f"  Total asientos PENDIENTE en staging: {len(pend_keys)}")
print(f"  >> YA EXISTEN en Contasis (duplicados que bloquean): {len(ya_existen)}")
print(f"  >> NO existen en Contasis (migrables sin conflicto): {len(no_existen)}")
if ya_existen:
    print("  Ejemplos de duplicados (max 15):")
    for k in ya_existen[:15]:
        print(f"    {k[0]}-{k[1]}-{k[2]}-{k[3]}")

# ── 5. Asientos MIGRADO en staging que NO estan en Contasis (migracion incompleta/perdida) ──
print("\n--- 5. Asientos MIGRADO en staging que NO estan en Contasis ---")
mig = db.execute(text("""
    SELECT DISTINCT cper, cmes, TRIM(ccodori) AS ccodori, nasiento
    FROM cf_diariol
    WHERE company_id = :cid AND estado = 'MIGRADO'
"""), {"cid": company_id}).fetchall()
mig_keys = [(str(r.cper), str(r.cmes), str(r.ccodori), int(r.nasiento) if r.nasiento is not None else None) for r in mig]
perdidos = [k for k in mig_keys if k not in contasis_keys]
print(f"  Total asientos MIGRADO en staging: {len(mig_keys)}")
print(f"  >> Marcados MIGRADO pero AUSENTES en Contasis: {len(perdidos)}")
if perdidos:
    print("  Ejemplos (max 15):")
    for k in perdidos[:15]:
        print(f"    {k[0]}-{k[1]}-{k[2]}-{k[3]}")

final_engine.dispose()
db.close()
print("\n===== FIN VERIFICACION (no se modifico ningun dato) =====")
