import sys
sys.path.append("c:\\SistemaMigConta")

from backend.app.core.database import get_dest_db
from sqlalchemy import text

db = next(get_dest_db())
try:
    # 1. Query cf_diariol
    staging = db.execute(text("SELECT id, company_id, subcategoria_id, idcontrol, estado FROM cf_diariol WHERE company_id = 4 AND subcategoria_id = 28 AND idcontrol = '005-FACT-I010001432'")).fetchall()
    print("Staging rows:", staging)
    
    # 2. Query vtaritem
    raw = db.execute(text("SELECT idcontrol, company_id FROM vtaritem WHERE company_id = 4 AND idcontrol = '005-FACT-I010001432'")).fetchall()
    print("Raw rows:", raw)
    
finally:
    db.close()
