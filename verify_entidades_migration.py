from backend.app.core.database import DestSessionLocal
from sqlalchemy import text

db = DestSessionLocal()

print("=== VERIFICACIÓN DE MIGRACIÓN DE ENTIDADES ===\n")

# Verificar datos en cg_entitrib por company_id
result = db.execute(text("SELECT company_id, COUNT(*) FROM cg_entitrib GROUP BY company_id ORDER BY company_id")).fetchall()
print("Registros en cg_entitrib por company_id:")
for row in result:
    print(f"  company_id {row[0]}: {row[1]} registros")

# Verificar si hay registros con estado='1' (para migración)
result = db.execute(text("SELECT COUNT(*) FROM cg_entitrib WHERE estado = '1'")).scalar()
print(f"\nRegistros con estado='1' en cg_entitrib: {result}")

# Verificar si hay registros con subcategoria_id
result = db.execute(text("SELECT subcategoria_id, COUNT(*) FROM cg_entitrib WHERE subcategoria_id IS NOT NULL GROUP BY subcategoria_id")).fetchall()
print(f"\nRegistros por subcategoria_id en cg_entitrib:")
for row in result:
    print(f"  subcategoria_id {row[0]}: {row[1]} registros")

# Verificar caracteres especiales en cg_entitrib
result = db.execute(text("""
    SELECT crazsoc, ccodruc 
    FROM cg_entitrib 
    WHERE crazsoc IS NOT NULL 
    AND (crazsoc LIKE '%á%' OR crazsoc LIKE '%é%' OR crazsoc LIKE '%í%' OR crazsoc LIKE '%ó%' OR crazsoc LIKE '%ú%' OR crazsoc LIKE '%ñ%')
    LIMIT 5
""")).fetchall()
print(f"\nEjemplos de registros con caracteres especiales en cg_entitrib:")
for row in result:
    print(f"  RUC: {row[1]}, Razón Social: {row[0]}")

db.close()
