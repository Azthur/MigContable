import pandas as pd
from sqlalchemy import create_engine
from backend.app.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.POSTGRES_CONNECTION_STRING)

# Get all columns of ccbrrdoc
all_cols_df = pd.read_sql('SELECT * FROM "ccbrrdoc" WHERE "company_id" = 1 LIMIT 1', engine)
print("All columns in ccbrrdoc:")
print(list(all_cols_df.columns))

# Let's inspect some of the specific columns that might have casing issues
# Like CodDoc, FchDoc, fchdoc, C_fechaNC, C_fechaEmision, C_fechaNC_Contasis
possible_cols = ["CodDoc", "FchDoc", "fchdoc", "C_fechaNC", "C_fechaEmision", "C_fechaNC_Contasis", "C_coddoc"]
existing_cols = [c for c in possible_cols if c in all_cols_df.columns]

query = f'SELECT "company_id", {", ".join([f'"{c}"' for c in existing_cols])} FROM "ccbrrdoc" WHERE "company_id" = 1 LIMIT 10'
print("\nRunning query:", query)
df = pd.read_sql(query, engine)
print("\nData:")
print(df)
print("\nDF Info:")
print(df.info())
