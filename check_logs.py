import sys, os
sys.path.append(os.getcwd())
from backend.app.core.database import dest_engine
from sqlalchemy import text
import pandas as pd

with dest_engine.connect() as conn:
    df = pd.read_sql(text('SELECT process_name, message FROM integ_logs ORDER BY id DESC LIMIT 10'), conn)
    for i, r in df.iterrows():
        print(f"{r['process_name']}: {r['message']}")
