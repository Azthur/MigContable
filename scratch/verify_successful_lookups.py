from backend.app.core.database import DestSessionLocal
from sqlalchemy import text
import pandas as pd

db = DestSessionLocal()
try:
    # Fetch 20 rows where codref1 is not null and print them
    query = text('SELECT "C_car", "codref1", "C_moneda", "C_tipoNC", "C_SerieNC", "C_numeroNC", "C_fechaNC_Contasis" FROM "ccbrrdoc" WHERE company_id = 1 AND "codref1" IS NOT NULL LIMIT 20')
    df = pd.read_sql(query, db.bind)
    
    print("Populated lookup records in ccbrrdoc:")
    print(df.to_string(index=False))
finally:
    db.close()
