import pandas as pd
from sqlalchemy import create_engine
from backend.app.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.POSTGRES_CONNECTION_STRING)

# Check all non-null values of C_fechaEmision in the database
df = pd.read_sql('SELECT "C_car", "fchdoc", "C_fechaEmision", "C_fechaNC", "C_fechaNC_Contasis" FROM "ccbrrdoc" WHERE "company_id" = 1 AND "C_fechaEmision" IS NOT NULL', engine)
print("Count of non-null C_fechaEmision rows:", len(df))
if len(df) > 0:
    print(df.head(10))

# Check all non-empty values of C_fechaEmision (sometimes saved as empty string)
df_non_empty = pd.read_sql('SELECT "C_car", "fchdoc", "C_fechaEmision", "C_fechaNC", "C_fechaNC_Contasis" FROM "ccbrrdoc" WHERE "company_id" = 1 AND "C_fechaEmision" != \'\'', engine)
print("Count of non-empty C_fechaEmision rows:", len(df_non_empty))
if len(df_non_empty) > 0:
    print(df_non_empty.head(10))
