import sys
import os
sys.path.append(os.getcwd())

from sqlalchemy import create_engine, text

DB_URL = "postgresql://postgres:postgres@localhost:5433/migconta_db"

def migrate_schema():
    engine = create_engine(DB_URL)
    
    print("Migrating schema to add new configuration columns...")
    try:
        with engine.begin() as conn:
            # Add to MapeoSubcategoria
            conn.execute(text("ALTER TABLE mapeo_subcategorias ADD COLUMN IF NOT EXISTS col_destino_nasiento VARCHAR(100)"))
            conn.execute(text("ALTER TABLE mapeo_subcategorias ADD COLUMN IF NOT EXISTS col_destino_nidlin VARCHAR(100)"))
            
            # Add JSON extra_data to staging tables
            conn.execute(text("ALTER TABLE cf_diariol ADD COLUMN IF NOT EXISTS extra_data JSON"))
            conn.execute(text("ALTER TABLE cf_diario ADD COLUMN IF NOT EXISTS extra_data JSON"))
            
            print("Successfully altered tables.")
    except Exception as e:
        print(f"Error migrating schema: {e}")

if __name__ == "__main__":
    migrate_schema()
