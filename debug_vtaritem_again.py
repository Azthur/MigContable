import sys, os
sys.path.append(os.getcwd())
from backend.app.core.database import dest_engine
from sqlalchemy import text
import pandas as pd

with dest_engine.connect() as conn:
    print('Checking formulas...')
    df = pd.read_sql(text("SELECT message FROM integ_logs WHERE process_name LIKE '%vtaritem%' ORDER BY id DESC LIMIT 2"), conn)
    for index, m in df.iterrows():
        print(f"LOG: {m['message']}")

    print('\nChecking IDCONTROL...')
    df2 = pd.read_sql(text("SELECT idcontrol, \"C_PrudctoCodigo\" FROM vtaritem WHERE idcontrol = '005-FACT-I030000005'"), conn)
    for index, row in df2.iterrows():
        print(f"Row {row['idcontrol']}: {row['C_PrudctoCodigo']}")
