import sys
import os
sys.path.append(os.getcwd())

from backend.app.core.database import dest_engine
from sqlalchemy import inspect

def list_db_tables():
    inspector = inspect(dest_engine)
    schemas = inspector.get_schema_names()
    print(f"Schemas found: {schemas}")
    
    for schema in schemas:
        if schema in ['information_schema', 'pg_catalog']: continue
        print(f"\nTables in schema '{schema}':")
        tables = inspector.get_table_names(schema=schema)
        for table in tables:
            print(f" - {table}")

if __name__ == "__main__":
    list_db_tables()
