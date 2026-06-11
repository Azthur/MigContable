import pandas as pd
from sqlalchemy import create_engine
from backend.app.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.POSTGRES_CONNECTION_STRING)

query = 'SELECT "company_id", "CodDoc", "NroDoc", "fchdoc", "C_fechaNC", "C_fechaEmision", "C_fechaNC_Contasis" FROM "ccbrrdoc" WHERE "_migration_id" = \'83a47cb6-b1d3-41a7-8bc8-e5c7b2db94b9\''
df = pd.read_sql(query, engine)
print("Row from database:")
print(df)
