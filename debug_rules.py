import sys, os
sys.path.append(os.getcwd())
from backend.app.core.database import dest_engine
from sqlalchemy import text
import pandas as pd

with dest_engine.connect() as conn:
    df = pd.read_sql(text('SELECT id, new_column_name FROM computed_column_rules WHERE company_id = 4'), conn)
    for index, r in df.iterrows():
        if 'PRUDCTO' in str(r['new_column_name']).upper():
            print(f"Rule ID {r['id']}: {r['new_column_name']}")
