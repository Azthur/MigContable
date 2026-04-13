import sys, os
import pandas as pd
sys.path.append(os.getcwd())
from backend.app.core.database import dest_engine
from sqlalchemy import text
with dest_engine.connect() as conn:
    df = pd.read_sql(text("SELECT \"C_estado1\" FROM vtaritem WHERE company_id = 4"), conn)
    counts = df['C_estado1'].value_counts(dropna=False)
    print(counts)
