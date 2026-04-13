import sys, os
import pandas as pd
sys.path.append(os.getcwd())
from backend.app.core.database import dest_engine
from sqlalchemy import text
with dest_engine.connect() as conn:
    df = pd.read_sql(text("SELECT data FROM user_catalog_items WHERE catalog_id = 26"), conn)
    for index, row in df.iterrows():
        val_cod = str(row['data']['COD_PROD'])
        val_cat = str(row['data']['CATEGORIA'])
        if 'I000000013' in val_cod or 'I000000013' in val_cat:
            print(f"Found I000000013: {row['data']}")
