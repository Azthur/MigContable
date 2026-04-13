import sys, os
sys.path.append(os.getcwd())
from backend.app.core.database import dest_engine
from sqlalchemy import text
import pandas as pd

with dest_engine.connect() as conn:
    df = pd.read_sql(text("SELECT id, table_selection_id, new_column_name, is_active FROM computed_column_rules"), conn)
    for index, r in df.iterrows():
        n = str(r['new_column_name'])
        if 'PRUDCT' in n.upper():
            print(f"Rule ID {r['id']} (active: {r['is_active']}): {repr(n)}")
