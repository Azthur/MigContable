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
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    print(df[["company_id", "NroDoc", "Codigo", "fchdoc", "C_fechaEmision", "C_fechaNC_Contasis", "idcontrol", "_migration_id"]])
