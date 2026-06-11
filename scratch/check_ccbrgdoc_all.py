import os
import sys
# Add parent dir to PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from backend.app.core.database import dest_engine

query = "SELECT company_id, count(*), count(fchdoc) FROM ccbrgdoc WHERE \"C_car\" = 'N/AB050000015' GROUP BY company_id"
df = pd.read_sql(query, dest_engine)
print("ccbrgdoc counts for N/AB050000015:")
print(df)
