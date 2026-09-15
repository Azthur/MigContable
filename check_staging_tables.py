from backend.app.core.database import DestSessionLocal
from sqlalchemy import text

db = DestSessionLocal()

# Buscar tablas que tengan columnas de staging (estado, subcategoria_id, company_id)
result = db.execute(text("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name NOT LIKE 'pg_%'
    AND table_name NOT LIKE 'sql_%'
    ORDER BY table_name
""")).fetchall()

print("=== TABLAS EN LA BASE DE DATOS ===")
staging_tables = []
for row in result:
    table_name = row[0]
    # Verificar si tiene columnas de staging
    cols_result = db.execute(text(f"""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = '{table_name}' 
        AND column_name IN ('estado', 'subcategoria_id', 'lote_id')
    """)).fetchall()
    
    if cols_result:
        staging_cols = [c[0] for c in cols_result]
        print(f"  {table_name} (staging: {staging_cols})")
        staging_tables.append(table_name)
    else:
        print(f"  {table_name}")

print(f"\n=== TABLAS DE STAGING ENCONTRADAS: {len(staging_tables)} ===")
for table in staging_tables:
    print(f"  {table}")

db.close()
