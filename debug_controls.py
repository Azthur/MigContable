import sys, os
sys.path.append(os.getcwd())
import pandas as pd
from backend.app.core.database import dest_engine
from sqlalchemy import text

with dest_engine.connect() as conn:
    df = pd.read_sql(text("SELECT id, company_id, source_table, control_column, last_migrated_value FROM migration_controls WHERE company_id = 4"), conn)
    print(df.to_string())
