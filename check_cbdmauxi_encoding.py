from backend.app.core.database import DestSessionLocal
from sqlalchemy import text

db = DestSessionLocal()

print("=== VERIFICACIÓN DE ENCODING EN cbdmauxi ===\n")

# Verificar caracteres especiales en cbdmauxi
result = db.execute(text("""
    SELECT nomaux, rucaux 
    FROM cbdmauxi 
    WHERE nomaux IS NOT NULL 
    AND (nomaux LIKE '%┬%' OR nomaux LIKE '%á%' OR nomaux LIKE '%é%' OR nomaux LIKE '%í%' OR nomaux LIKE '%ó%' OR nomaux LIKE '%ú%' OR nomaux LIKE '%ñ%')
    LIMIT 10
""")).fetchall()

print(f"Registros con caracteres especiales en cbdmauxi: {len(result)}")
for row in result:
    print(f"  RUC: {row[1]}, Nombre: {row[0]}")

# Verificar registros con caracteres corruptos específicos
result = db.execute(text("""
    SELECT nomaux, rucaux 
    FROM cbdmauxi 
    WHERE nomaux IS NOT NULL 
    AND nomaux LIKE '%┬%'
    LIMIT 5
""")).fetchall()

print(f"\nRegistros con caracteres corruptos (┬) en cbdmauxi: {len(result)}")
for row in result:
    print(f"  RUC: {row[1]}, Nombre: {row[0]}")

db.close()
