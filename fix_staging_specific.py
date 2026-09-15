from backend.app.core.database import DestSessionLocal
from sqlalchemy import text

db = DestSessionLocal()

print("=== CORRECCIÓN ESPECÍFICA EN STAGING LOCAL ===\n")

# Corregir el RUC 20609635810 específicamente
result = db.execute(text("""
    UPDATE cg_entitrib 
    SET crazsoc = 'SELHA SALON SPA S.A.C. - SELHA SALON S.A.C.'
    WHERE ccodruc = '20609635810'
"""))

db.commit()

print(f"Registros actualizados para 20609635810: {result.rowcount}")

# Corregir el RUC 20557566512 específicamente
result = db.execute(text("""
    UPDATE cg_entitrib 
    SET crazsoc = 'VILROSES SALON & ANDEAN SPA S.A'
    WHERE ccodruc = '20557566512'
"""))

db.commit()

print(f"Registros actualizados para 20557566512: {result.rowcount}")

# Corregir el RUC 10316740958 específicamente (Dé -> D')
result = db.execute(text("""
    UPDATE cg_entitrib 
    SET crazsoc = 'SALON & SPA D''ANGELO'
    WHERE ccodruc = '10316740958'
"""))

db.commit()

print(f"Registros actualizados para 10316740958: {result.rowcount}")

db.close()
