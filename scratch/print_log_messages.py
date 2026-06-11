import pandas as pd
from sqlalchemy import create_engine
from backend.app.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.POSTGRES_CONNECTION_STRING)

# Get the last 10 logs with process_name, status, and message
df = pd.read_sql('SELECT id, process_name, status, message, records_processed FROM integ_logs WHERE company_id = 1 ORDER BY id DESC LIMIT 10', engine)
pd.set_option('display.max_colwidth', None)
for idx, row in df.iterrows():
    print(f"Log ID: {row['id']} | Process: {row['process_name']} | Status: {row['status']} | Records: {row['records_processed']}")
    print(f"Message: {row['message']}\n" + "-"*80)
