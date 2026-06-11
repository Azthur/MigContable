import os
import sys
# Add parent dir to PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from backend.app.core.database import dest_engine

query = 'SELECT * FROM ccbrrdoc WHERE "NroDoc" = \'B050000015\''
df = pd.read_sql(query, dest_engine)
if df.empty:
    print("No rows found")
else:
    # Print the entire dataframe to a CSV or text file to inspect
    df.to_csv("c:\\SistemaMigConta\\scratch\\ccbrrdoc_b05_all.csv", index=False)
    print(f"Saved {len(df)} rows to ccbrrdoc_b05_all.csv")
    print(df[["company_id", "Codigo", "fchdoc", "C_fechaEmision", "C_fechaNC_Contasis", "_migration_id"]])
