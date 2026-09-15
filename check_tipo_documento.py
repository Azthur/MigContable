from backend.app.core.database import DestSessionLocal
from sqlalchemy import text

db = DestSessionLocal()

print("=== ANÁLISIS DE TIPO DE DOCUMENTO EN cbdmauxi ===\n")

# Verificar valores de tpodoc
result = db.execute(text("SELECT DISTINCT tpodoc, COUNT(*) FROM cbdmauxi GROUP BY tpodoc ORDER BY tpodoc")).fetchall()
print("Valores de tpodoc:")
for row in result:
    print(f"  tpodoc: '{row[0]}' ({row[1]} registros)")

# Verificar valores de C_tipoauxiliar
result = db.execute(text('SELECT DISTINCT "C_tipoauxiliar", COUNT(*) FROM cbdmauxi WHERE "C_tipoauxiliar" IS NOT NULL GROUP BY "C_tipoauxiliar" ORDER BY "C_tipoauxiliar"')).fetchall()
print("\nValores de C_tipoauxiliar:")
for row in result:
    print(f"  C_tipoauxiliar: '{row[0]}' ({row[1]} registros)")

# Verificar mapeo entre tpodoc y rucaux (RUC)
result = db.execute(text("SELECT tpodoc, COUNT(*) FROM cbdmauxi WHERE rucaux IS NOT NULL AND LENGTH(rucaux) = 11 GROUP BY tpodoc ORDER BY tpodoc")).fetchall()
print("\nDistribución de tpodoc para registros con RUC (11 dígitos):")
for row in result:
    print(f"  tpodoc: '{row[0]}' ({row[1]} registros)")

# Verificar mapeo entre tpodoc y rucaux (DNI)
result = db.execute(text("SELECT tpodoc, COUNT(*) FROM cbdmauxi WHERE rucaux IS NOT NULL AND LENGTH(rucaux) = 8 GROUP BY tpodoc ORDER BY tpodoc")).fetchall()
print("\nDistribución de tpodoc para registros con DNI (8 dígitos):")
for row in result:
    print(f"  tpodoc: '{row[0]}' ({row[1]} registros)")

# Ejemplos de datos
result = db.execute(text("SELECT tpodoc, rucaux, nomaux, \"C_tipoauxiliar\" FROM cbdmauxi WHERE rucaux IS NOT NULL LIMIT 10")).fetchall()
print("\nEjemplos de datos:")
for row in result:
    print(f"  tpodoc: '{row[0]}', RUC/DNI: '{row[1]}', Nombre: '{row[2]}', C_tipoauxiliar: '{row[3]}'")

db.close()
