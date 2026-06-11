import os
import sys
# Add parent dir to PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from backend.app.core.database import dest_engine

query = "SELECT company_id, count(*) FROM ccbrrdoc GROUP BY company_id"
df = pd.read_sql(query, dest_engine)
print("Counts by company_id in ccbrrdoc:")
print(df)

query2 = "SELECT id, name FROM companies"
df2 = pd.read_sql(query2, dest_engine)
print("\nCompanies list:")
print(df2)
