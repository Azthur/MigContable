import pandas as pd
import ast
import re
from sqlalchemy import create_engine
from backend.app.core.config import get_settings
from backend.app.core.formula_parser import evaluate_formula_on_df
from backend.app.core.database import get_dest_db

settings = get_settings()
engine = create_engine(settings.POSTGRES_CONNECTION_STRING)

# Let's load the data from PostgreSQL for company_id = 1
# We want to load ccbrrdoc and test how the formulas are applied in memory.
df = pd.read_sql('SELECT * FROM "ccbrrdoc" WHERE "company_id" = 1', engine)
print("DataFrame columns:")
print(list(df.columns))

# Let's inspect fchdoc
print("\nfchdoc Series summary:")
print(df["fchdoc"].describe())
print(df["fchdoc"].head(10))

# Let's test the evaluation of LEFT(fchdoc, 10)
# We will simulate Session because evaluate_formula_on_df takes db Session
# but doesn't use it if the formula doesn't have BUSCARX/BUSCARX_EXT.
print("\nEvaluating LEFT(fchdoc, 10)...")
res_emision = evaluate_formula_on_df(df, "LEFT(fchdoc, 10)", None, 1)
print("LEFT(fchdoc, 10) result:")
print(res_emision.describe())
print(res_emision.head(10))

# Let's check if there are non-empty values
non_empty = res_emision[res_emision.str.strip() != ""]
print("\nNon-empty results count:", len(non_empty))
if len(non_empty) > 0:
    print("Non-empty samples:")
    print(non_empty.head(10))
