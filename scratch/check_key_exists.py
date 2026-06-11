import pandas as pd
from sqlalchemy import create_engine
from backend.app.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.POSTGRES_CONNECTION_STRING)

# Check if N/AA010000295 exists in ccbrgdoc
df_g = pd.read_sql('SELECT "company_id", "C_car", "fchdoc" FROM "ccbrgdoc" WHERE "company_id" = 1 AND "C_car" = \'N/AA010000295\'', engine)
print("ccbrgdoc rows for N/AA010000295:")
print(df_g)

# Let's count how many distinct C_car keys exist in ccbrrdoc vs ccbrgdoc
df_cnt = pd.read_sql('''
    SELECT 
        (SELECT COUNT(DISTINCT "C_car") FROM "ccbrrdoc" WHERE "company_id" = 1) as unique_rr_keys,
        (SELECT COUNT(DISTINCT "C_car") FROM "ccbrgdoc" WHERE "company_id" = 1) as unique_rg_keys,
        (SELECT COUNT(DISTINCT r."C_car") FROM "ccbrrdoc" r JOIN "ccbrgdoc" g ON r."C_car" = g."C_car" WHERE r."company_id" = 1 AND g."company_id" = 1) as matching_keys
''', engine)
print("\nUnique and matching keys count:")
print(df_cnt)
