import sys, os
sys.path.append(os.getcwd())
from backend.app.core.database import dest_engine
from sqlalchemy import text
import pandas as pd

with dest_engine.connect() as conn:
    df = pd.read_sql(text("SELECT id, new_column_name, condition_value, result_value FROM computed_column_rules WHERE UPPER(new_column_name) LIKE '%PRUDCTO%'"), conn)
    for index, row in df.iterrows():
        print(f"Rule ID {row['id']}: {row['new_column_name']}")
        print(f"  Condition: {row['condition_value']}")
        print(f"  Result:    {row['result_value']}")
