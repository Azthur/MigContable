import pandas as pd
from sqlalchemy import create_engine, text
from backend.app.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.POSTGRES_CONNECTION_STRING)

# Check recent ETL logs
logs_df = pd.read_sql('SELECT id, process_name, status, message, records_processed, created_at FROM integ_logs WHERE company_id = 1 ORDER BY id DESC LIMIT 10', engine)
print("Recent ETL logs:")
print(logs_df)

# Check count of non-null and null in ccbrrdoc
cnt_df = pd.read_sql('SELECT COUNT(*) as total, COUNT("C_fechaEmision") as non_null_emision, COUNT("C_fechaNC_Contasis") as non_null_nc FROM "ccbrrdoc" WHERE "company_id" = 1', engine)
print("\nccbrrdoc counts:")
print(cnt_df)

# Let's inspect rows that might be NULL and print a few to see what they contain
df_null = pd.read_sql('SELECT "C_car", "fchdoc", "C_fechaEmision", "C_fechaNC_Contasis" FROM "ccbrrdoc" WHERE "company_id" = 1 LIMIT 5', engine)
print("\nFirst 5 rows in ccbrrdoc:")
print(df_null)
