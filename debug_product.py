import sys, os
import pandas as pd
sys.path.append(os.getcwd())
from backend.app.core.database import dest_engine
from sqlalchemy import text
with dest_engine.connect() as conn:
    df = pd.read_sql(text("SELECT \"C_Producto\" FROM vtaritem WHERE idcontrol = '005-FACT-I030000005' LIMIT 1"), conn)
    for index, row in df.iterrows():
        print(f"C_Producto: {row['C_Producto']}")
