import sys
sys.path.append("c:\\SistemaMigConta")
from backend.app.core.database import DestSessionLocal
from backend.app.models.models import CfDiariol

db = DestSessionLocal()

company_id = 1
subcategoria_id = 4 # Registro de Ventas (vtaritem)

query_del = db.query(CfDiariol).filter(
    CfDiariol.company_id == company_id,
    CfDiariol.estado == "PENDIENTE"
)
if subcategoria_id:
    query_del = query_del.filter(CfDiariol.subcategoria_id == subcategoria_id)

count = query_del.count()
print(f"Records to delete: {count}")

try:
    del_count = query_del.delete(synchronize_session=False)
    db.commit()
    print(f"Deleted: {del_count}")
except Exception as e:
    db.rollback()
    print("Error deleting:", e)

leftover = db.query(CfDiariol).filter(CfDiariol.subcategoria_id == subcategoria_id).count()
print(f"Leftover for sub {subcategoria_id}: {leftover}")
