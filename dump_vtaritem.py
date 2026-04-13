import sys, os
sys.path.append(os.getcwd())
from backend.app.core.database import dest_engine
from sqlalchemy import text
import pandas as pd

with dest_engine.connect() as conn:
    print('Checking vtaritem...')
    try:
        df = pd.read_sql(text('SELECT * FROM "vtaritem" LIMIT 5'), conn)
        df.to_csv('vtaritem_sample.csv', index=False)
        print('Saved to vtaritem_sample.csv')
    except Exception as e:
        print(f'Error reading vtaritem: {e}')
