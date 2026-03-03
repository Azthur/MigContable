import sys
sys.path.insert(0, r"c:\SistemaMigConta")
from backend.app.core.database import dest_engine
from sqlalchemy import text
import pandas as pd

query = "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
with dest_engine.connect() as conn:
    tables = [r[0] for r in conn.execute(text(query)).fetchall()]

found = False
for t in tables:
    try:
        with dest_engine.connect() as conn:
            df = pd.read_sql(f'SELECT * FROM "{t}"', conn)
            # search all string columns for SI.CONJUNTO
            for col in df.columns:
                if df[col].dtype == object:
                    matches = df[df[col].astype(str).str.contains("SI.CONJUNTO", regex=False, na=False)]
                    if not matches.empty:
                        print(f"FOUND IN TABLE {t}, COLUMN {col}:")
                        print(matches[col].unique())
                        found = True
    except Exception as e:
        pass

if not found:
    print("NOT FOUND ANYWHERE IN DESTINATION DATABASE")
