from backend.app.core.database import DestSessionLocal
from sqlalchemy import text

db = DestSessionLocal()

# Verificar datos en cbdmauxi
result = db.execute(text("SELECT COUNT(*) FROM cbdmauxi")).scalar()
print(f"Total registros en cbdmauxi: {result}")

# Verificar datos por empresa
result = db.execute(text("SELECT codcia, COUNT(*) FROM cbdmauxi GROUP BY codcia")).fetchall()
print(f"\nRegistros por empresa (codcia):")
for row in result:
    print(f"  codcia {row[0]}: {row[1]} registros")

# Verificar datos en cg_entitrib (destino final)
result = db.execute(text("SELECT COUNT(*) FROM cg_entitrib")).scalar()
print(f"\nTotal registros en cg_entitrib (destino final): {result}")

# Verificar si existe tabla de staging para entidades
try:
    result = db.execute(text("SELECT COUNT(*) FROM cg_entitrib WHERE estado = 'PENDIENTE'")).scalar()
    print(f"Registros PENDIENTE en cg_entitrib (staging): {result}")
except Exception as e:
    print(f"No hay columna estado en cg_entitrib: {e}")

db.close()
