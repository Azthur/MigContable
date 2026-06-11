import pandas as pd
from sqlalchemy import create_engine
from backend.app.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.POSTGRES_CONNECTION_STRING)

# Query the row in ccbrrdoc where C_car is N/AM010003564
query = '''
    SELECT "C_car", "fchdoc", "C_fechaNC", "C_fechaEmision", "C_fechaNC_Contasis" 
    FROM "ccbrrdoc" 
    WHERE "company_id" = 1 AND "C_car" = 'N/AM010003564'
'''
df = pd.read_sql(query, engine)
print("ccbrrdoc row for N/AM010003564:")
print(df)
