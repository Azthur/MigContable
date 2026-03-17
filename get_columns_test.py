import pandas as pd
from backend.app.core.database import dest_engine

def test():
    try:
        # We know one of the tables is 'ccbmvtos' or something similar
        query = "SELECT * FROM information_schema.columns WHERE table_name LIKE '%ccbmvtos%' OR table_name LIKE '%mvtos%'"
        df = pd.read_sql(query, dest_engine)
        tables = df['table_name'].unique()
        for t in tables:
            print(f"--- Columns for {t} ---")
            cols = df[df['table_name'] == t]['column_name'].tolist()
            print([c for c in cols if 'mon' in c.lower() or 'cod' in c.lower()])
            
        # also read 1 row from the table to see exact columns
        if len(tables) > 0:
            df_data = pd.read_sql(f'SELECT * FROM "{tables[0]}" LIMIT 1', dest_engine)
            print("Row columns:")
            print(df_data.columns.tolist())
            
    except Exception as e:
        print("Error:", e)

test()
