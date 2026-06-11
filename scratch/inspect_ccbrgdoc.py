import pandas as pd
from sqlalchemy import create_engine
from backend.app.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.POSTGRES_CONNECTION_STRING)

# Get all columns of ccbrgdoc
all_cols_df = pd.read_sql('SELECT * FROM "ccbrgdoc" WHERE "company_id" = 1 LIMIT 1', engine)
print("All columns in ccbrgdoc:")
print(list(all_cols_df.columns))

# Query a few rows of ccbrgdoc to check values of C_car, fchdoc, C_fechaNC
# (we want to check if C_car matches C_car in ccbrrdoc)
possible_cols = ["C_car", "fchdoc", "FchDoc", "FCHDOC", "C_fechaNC"]
existing_cols = [c for c in possible_cols if c in all_cols_df.columns]

query = f'SELECT "company_id", {", ".join([f'"{c}"' for c in existing_cols])} FROM "ccbrgdoc" WHERE "company_id" = 1 LIMIT 10'
print("\nRunning query:", query)
df = pd.read_sql(query, engine)
print("\nData from ccbrgdoc:")
print(df)
