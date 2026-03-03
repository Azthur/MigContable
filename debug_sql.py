import pandas as pd
from sqlalchemy import create_engine
engine = create_engine('postgresql://postgres:postgres@localhost:5433/migconta_db')
df1 = pd.read_sql('SELECT "C_car", "C_tipocliente" FROM ccbrgdoc LIMIT 5', engine)
df2 = pd.read_sql('SELECT "C_car" FROM vtaritem LIMIT 5', engine)
print('ccbrgdoc samples:')
print(df1)
print('vtaritem samples:')
print(df2)
