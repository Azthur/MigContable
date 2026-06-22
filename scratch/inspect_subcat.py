from backend.app.core.database import DestSessionLocal, dest_engine
from backend.app.models.models import MapeoSubcategoria
from sqlalchemy import Table, MetaData, inspect

from backend.app.core.database import DestSessionLocal, dest_engine
from backend.app.models.models import MapeoSubcategoria, MapeoCategoria
from sqlalchemy import Table, MetaData, inspect

db = DestSessionLocal()
try:
    subs = db.query(MapeoSubcategoria).join(MapeoCategoria).filter(MapeoCategoria.company_id == 4).all()
    print(f"Found {len(subs)} subcategories for company 4:")
    insp = inspect(dest_engine)
    for sub in subs:
        table_name = sub.tabla_destino_detalle or "cf_diariol"
        has_table = insp.has_table(table_name)
        has_idcontrol = False
        if has_table:
            columns = [c['name'] for c in insp.get_columns(table_name)]
            has_idcontrol = 'idcontrol' in columns
        print(f"ID: {sub.id} | Name: {sub.nombre} | Staging Table: {table_name} | Exists: {has_table} | Has idcontrol: {has_idcontrol}")
finally:
    db.close()
