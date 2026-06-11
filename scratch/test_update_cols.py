import pandas as pd
from sqlalchemy import create_engine, inspect
from backend.app.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.POSTGRES_CONNECTION_STRING)

# Inspect column types of ccbrrdoc in PostgreSQL
insp = inspect(engine)
col_info_list = insp.get_columns("ccbrrdoc")
dest_type_map = {c['name']: str(c['type']).upper() for c in col_info_list}

print("Columns and types of ccbrrdoc:")
for name, col_type in dest_type_map.items():
    if "fecha" in name.lower() or "fchdoc" in name.lower():
        print(f"Col: {name} | Type: {col_type}")
