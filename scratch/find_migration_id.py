import os
import sys
# Add parent dir to PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect, text
from backend.app.core.database import dest_engine

db_engine = dest_engine
inspector = inspect(db_engine)
target_id = "83a47cb6-b1d3-41a7-8bc8-e5c7b2db94b9"

for table_name in inspector.get_table_names():
    cols = [c['name'] for c in inspector.get_columns(table_name)]
    # Check if _migration_id exists in any case variation
    migration_col = next((c for c in cols if c.lower() == "_migration_id"), None)
    if migration_col:
        query = text(f'SELECT count(*) FROM "{table_name}" WHERE "{migration_col}" = :tid')
        with db_engine.connect() as conn:
            try:
                cnt = conn.execute(query, {"tid": target_id}).scalar()
                if cnt > 0:
                    print(f"Found {cnt} rows in table '{table_name}' with _migration_id = {target_id}")
                    # Print the row
                    query_row = text(f'SELECT * FROM "{table_name}" WHERE "{migration_col}" = :tid')
                    res = conn.execute(query_row, {"tid": target_id}).fetchone()
                    print(dict(zip(cols, res)))
            except Exception as e:
                print(f"Error checking {table_name}: {e}")
