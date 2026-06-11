import os
import sys
# Add parent dir to PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from backend.app.core.database import dest_engine

ids = ("83a47cb6-b1d3-41a7-8bc8-e5c7b2db94b9", "29a51c31-48f0-496c-9839-1c2b5d3fe637")
query = f"SELECT * FROM ccbrrdoc WHERE \"_migration_id\" IN {ids}"
df = pd.read_sql(query, dest_engine)
if df.empty:
    print("No rows found for these migration IDs")
else:
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    print(df[["NroDoc", "Codigo", "fchdoc", "C_fechaEmision", "C_fechaNC_Contasis", "_migration_id"]])
