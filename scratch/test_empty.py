import sys
sys.path.append('c:/SistemaMigConta')
from backend.app.core.database import DestSessionLocal
import pandas as pd
from sqlalchemy import text

db = DestSessionLocal()

df = pd.DataFrame({"test_col": ["", "Hello", None, "NaT"]})
df.to_sql("temp_empty_test", db.bind, if_exists="replace", index=False)

with db.bind.connect() as conn:
    res = conn.execute(text("SELECT * FROM temp_empty_test"))
    for row in res.fetchall():
        print(row)
