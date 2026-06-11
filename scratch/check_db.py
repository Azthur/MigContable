import os
import sys
sys.path.insert(0, os.path.abspath('backend'))
sys.path.insert(0, os.path.abspath('.'))

from app.core.database import DestSessionLocal
from sqlalchemy import text

db = DestSessionLocal()
try:
    # Query with exact migration ID
    query = text("""
        SELECT 
            "CodCia", "Anos", "TpoDoc", "CodDoc", "NroDoc", 
            "C_fechaEmision", "C_fechaNC_Contasis", "fchdoc", "C_fechaNC",
            "_migration_id", "company_id", "idcontrol"
        FROM ccbrrdoc 
        WHERE "_migration_id" = '83a47cb6-b1d3-41a7-8bc8-e5c7b2db94b9'
    """)
    res = db.execute(query).fetchall()
    print(f"Found with exact _migration_id '83a47cb6-b1d3-41a7-8bc8-e5c7b2db94b9':")
    for r in res:
        print(dict(r._mapping))
finally:
    db.close()
