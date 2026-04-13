import sys, os
sys.path.append(os.getcwd())
import pandas as pd
from backend.app.core.database import DestSessionLocal
from sqlalchemy import text
db = DestSessionLocal()
df = pd.read_sql(text("SELECT process_name, message, created_at FROM integ_logs WHERE company_id = 6 ORDER BY id DESC LIMIT 5"), db.get_bind())
print(df.to_string())
