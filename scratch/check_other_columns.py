import pandas as pd
from sqlalchemy import create_engine
from backend.app.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.POSTGRES_CONNECTION_STRING)

# Query a matching row to check all calculated columns
df = pd.read_sql('SELECT "C_car", "C_moneda", "codref1", "fchdoc", "C_fechaNC", "C_fechaEmision", "C_fechaNC_Contasis" FROM "ccbrrdoc" WHERE "company_id" = 1 AND "C_moneda" IS NOT NULL LIMIT 10', engine)
print("Matching rows:")
print(df)
