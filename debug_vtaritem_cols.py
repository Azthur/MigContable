import sys, os
sys.path.append(os.getcwd())
from backend.app.core.database import dest_engine
from sqlalchemy import text
import pandas as pd

with dest_engine.connect() as conn:
    print('Checking vtaritem columns inside docker...')
    df = pd.read_sql(text('SELECT * FROM vtaritem LIMIT 1'), conn)
    cols = sorted([str(c) for c in df.columns])
    for c in cols:
        print(f"  {c}")
