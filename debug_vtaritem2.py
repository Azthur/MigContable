import sys, os
sys.path.append(os.getcwd())
from backend.app.core.database import dest_engine
from sqlalchemy import text
import pandas as pd

with dest_engine.connect() as conn:
    print('\nChecking estado...')
    df2 = pd.read_sql(text('SELECT c_estado, "C_estado1" FROM vtaritem WHERE idcontrol = \'005-FACT-I030000005\''), conn)
    for index, row in df2.iterrows():
        print(f"Row c_estado: {row['c_estado']}, C_estado1: {row['C_estado1']}")
