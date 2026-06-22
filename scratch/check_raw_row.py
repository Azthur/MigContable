import sys
sys.path.append("c:\\SistemaMigConta")
from backend.app.core.database import DestSessionLocal
from backend.app.models.models import MapeoSubcategoria
from sqlalchemy import MetaData, Table, select

db = DestSessionLocal()
try:
    sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == 28).first()
    print("Subcategoria:", sub)
    if sub:
        print("id:", sub.id)
        print("nombre:", sub.nombre)
        print("tabla_origen:", sub.tabla_origen)
        
        raw_table_name = sub.tabla_origen.lower().replace(" ", "_")
        print("raw_table_name:", raw_table_name)
        
        metadata = MetaData()
        engine = db.get_bind()
        
        try:
            RawTable = Table(raw_table_name, metadata, autoload_with=engine)
            print("Columns in RawTable:", list(RawTable.c.keys()))
            
            stmt = select(RawTable).where(RawTable.c.idcontrol == '005-FACT-I010001432')
            if "company_id" in RawTable.c:
                stmt = stmt.where(RawTable.c.company_id == 4)
                print("Filtered by company_id = 4")
                
            res = db.execute(stmt).first()
            print("Row result:", res)
        except Exception as e:
            print("Error loading/querying table:", e)
finally:
    db.close()
