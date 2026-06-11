import os
import sys
# Add parent dir to PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from backend.app.core.database import dest_engine

query = "SELECT count(*) FROM ccbrrdoc WHERE company_id = 1 AND fchdoc IS NULL"
df = pd.read_sql(query, dest_engine)
print("Count of NULL fchdoc rows in ccbrrdoc for company 1:")
print(df)
