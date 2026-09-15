from backend.app.core.database import DestSessionLocal
from sqlalchemy import text, inspect

db = DestSessionLocal()

# Verificar estructura de cbdmauxi
insp = inspect(db.bind)
try:
    columns = insp.get_columns('cbdmauxi')
    print("=== ESTRUCTURA cbdmauxi ===")
    for col in columns:
        print(f"  {col['name']}: {col['type']}")
except Exception as e:
    print(f"Error obteniendo estructura cbdmauxi: {e}")

# Verificar si existe tabla de staging para entidades
print("\n=== BUSCANDO TABLAS DE STAGING ===")
result = db.execute(text("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name LIKE '%entit%'
    ORDER BY table_name
""")).fetchall()

for row in result:
    print(f"  {row[0]}")

# Verificar si cg_entitrib tiene columnas de staging
try:
    columns = insp.get_columns('cg_entitrib')
    print("\n=== ESTRUCTURA cg_entitrib ===")
    staging_cols = ['estado', 'subcategoria_id', 'lote_id', 'company_id']
    for col in columns:
        if col['name'] in staging_cols:
            print(f"  {col['name']}: {col['type']} (staging)")
        else:
            print(f"  {col['name']}: {col['type']}")
except Exception as e:
    print(f"Error obteniendo estructura cg_entitrib: {e}")

db.close()
