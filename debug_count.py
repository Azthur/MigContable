import sys, os
sys.path.append(os.getcwd())
import pandas as pd
from backend.app.core.database import dest_engine
from sqlalchemy import text

with dest_engine.connect() as conn:
    df = pd.read_sql(text("SELECT count(*) as total, company_id FROM vtaritem GROUP BY company_id"), conn)
    for index, row in df.iterrows():
        print(f"Company {row['company_id']}: {row['total']} records")
    
    df2 = pd.read_sql(text("SELECT idcontrol, \"C_PrudctoCodigo\" FROM vtaritem WHERE idcontrol = '005-FACT-I030000005'"), conn)
    for index, row in df2.iterrows():
        print(f"IDCONTROL 005-FACT-I030000005: {row['C_PrudctoCodigo']}")
