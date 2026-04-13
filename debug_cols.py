import sys, os
sys.path.append(os.getcwd())
import pandas as pd
from backend.app.core.database import DestSessionLocal
from sqlalchemy import text
db = DestSessionLocal()
df = pd.read_sql(text('SELECT * FROM "tbl_Conciliados" LIMIT 1'), db.get_bind())
print([c for c in df.columns if 'estado' in c.lower()])
