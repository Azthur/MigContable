import sys
sys.path.append("c:\\SistemaMigConta")
from backend.app.core.database import dest_engine
from sqlalchemy import text
import pandas as pd

with dest_engine.connect() as conn:
    df = pd.read_sql("SELECT * FROM mapeo_subcategorias WHERE tabla_origen = 'vtaritem'", conn)
    for col in df.columns:
        print(f"{col}: {df[col].iloc[0]}")
