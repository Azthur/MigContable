import pandas as pd
from sqlalchemy import create_engine
from backend.app.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.POSTGRES_CONNECTION_STRING)

# Get some C_car values from ccbrrdoc
rr_df = pd.read_sql('SELECT "CodDoc", "NroDoc", "C_car", "fchdoc", "C_fechaNC" FROM "ccbrrdoc" WHERE "company_id" = 1 LIMIT 20', engine)
print("ccbrrdoc sample rows:")
print(rr_df)

# Check if there are any exact matches of C_car between ccbrrdoc and ccbrgdoc
matching = pd.read_sql('''
    SELECT r."C_car" as r_car, g."C_car" as g_car, g.fchdoc, g."C_fechaNC"
    FROM "ccbrrdoc" r
    JOIN "ccbrgdoc" g ON r."C_car" = g."C_car"
    WHERE r."company_id" = 1 AND g."company_id" = 1
    LIMIT 10
''', engine)
print("\nMatching C_car rows via SQL JOIN:")
print(matching)

# Total matches count
total_matches = pd.read_sql('''
    SELECT COUNT(*) as cnt
    FROM "ccbrrdoc" r
    JOIN "ccbrgdoc" g ON r."C_car" = g."C_car"
    WHERE r."company_id" = 1 AND g."company_id" = 1
''', engine)
print("\nTotal matching C_car rows count:", total_matches.iloc[0]["cnt"])
