from backend.app.core.database import DestSessionLocal
from sqlalchemy import text
import pandas as pd

db = DestSessionLocal()
try:
    query = text('SELECT "CodDoc", "C_fechaNC", "C_fechaNC_Contasis" FROM "ccbrrdoc" WHERE company_id = 1 AND "codref1" IS NOT NULL LIMIT 20')
    df = pd.read_sql(query, db.bind)
    print(df.to_string(index=False))
finally:
    db.close()
