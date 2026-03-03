
import sys
import os
sys.path.append(os.getcwd())

from sqlalchemy import create_engine, text
from backend.app.core.database import DestBase
import backend.app.models.models  # Register models

DB_URL = "postgresql://postgres:postgres@localhost:5433/migconta_db"

def fix_schema():
    engine = create_engine(DB_URL)
    
    print("Dropping tables to allow regeneration...")
    try:
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS integ_logs CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS config_account_mapping CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS config_document_mapping CASCADE"))
            conn.commit()
            print("Dropped tables.")
    except Exception as e:
        print(f"Error dropping table: {e}")
        
    print("Re-creating tables...")
    try:
        DestBase.metadata.create_all(bind=engine)
        print("Tables created successfully.")
    except Exception as e:
        print(f"Error creating tables: {e}")

if __name__ == "__main__":
    fix_schema()
