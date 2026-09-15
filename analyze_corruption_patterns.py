from backend.app.core.database import DestSessionLocal
from sqlalchemy import text

db = DestSessionLocal()

print("=== ANÁLISIS DE PATRONES DE CORRUPCIÓN EN Contasis FINAL ===\n")

# Analizar crazsoc en Contasis final
result = db.execute(text("""
    SELECT crazsoc, ccodruc 
    FROM cg_entitrib 
    WHERE crazsoc IS NOT NULL 
    AND crazsoc LIKE '%┬%'
    LIMIT 10
""")).fetchall()

print(f"Registros con ┬ en crazsoc: {len(result)}")
for row in result:
    print(f"  RUC: {row[1]}, Razón Social: {row[0][:80]}")

# Analizar íÁ
result = db.execute(text("""
    SELECT crazsoc, ccodruc 
    FROM cg_entitrib 
    WHERE crazsoc IS NOT NULL 
    AND crazsoc LIKE '%íÁ%'
    LIMIT 10
""")).fetchall()

print(f"\nRegistros con íÁ en crazsoc: {len(result)}")
for row in result:
    print(f"  RUC: {row[1]}, Razón Social: {row[0][:80]}")

# Analizar otros caracteres corruptos
result = db.execute(text("""
    SELECT crazsoc, ccodruc 
    FROM cg_entitrib 
    WHERE crazsoc IS NOT NULL 
    AND (crazsoc LIKE '%┤%' OR crazsoc LIKE '%á%' OR crazsoc LIKE '%Á%')
    LIMIT 10
""")).fetchall()

print(f"\nRegistros con otros caracteres corruptos en crazsoc: {len(result)}")
for row in result:
    print(f"  RUC: {row[1]}, Razón Social: {row[0][:80]}")

db.close()
