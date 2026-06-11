import os
import sys
# Add parent dir to PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from backend.app.core.database import dest_engine

query = "SELECT * FROM ccbrgdoc WHERE \"C_car\" = 'N/AB050000015'"
df = pd.read_sql(query, dest_engine)
if df.empty:
    print("No rows found in ccbrgdoc for C_car = N/AB050000015")
else:
    print(f"Found {len(df)} rows in ccbrgdoc:")
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    cols = ["C_car", "fchdoc", "company_id"]
    cols_map = {c.lower(): c for c in df.columns}
    existing_cols = [cols_map[c.lower()] for c in cols if c.lower() in cols_map]
    print(df[existing_cols])
