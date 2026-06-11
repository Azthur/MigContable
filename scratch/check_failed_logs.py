import os
import sys
# Add parent dir to PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from backend.app.core.database import dest_engine

query = "SELECT id, process_name, status, SUBSTRING(message, 1, 200) as msg_short, SUBSTRING(details, 1, 200) as det_short, created_at FROM integ_logs WHERE status = 'ERROR' ORDER BY id DESC LIMIT 15"
df = pd.read_sql(query, dest_engine)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
pd.set_option('display.max_colwidth', None)
print(df)
