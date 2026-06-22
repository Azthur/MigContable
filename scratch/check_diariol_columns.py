import sys
sys.path.append("c:\\SistemaMigConta")

from backend.app.core.database import get_dest_db
from sqlalchemy import text

db = next(get_dest_db())
try:
    r = db.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'cf_diariol'")).fetchall()
    print("Columns in cf_diariol:")
    for col, dt in sorted(r):
        print(f" - {col}: {dt}")
finally:
    db.close()
