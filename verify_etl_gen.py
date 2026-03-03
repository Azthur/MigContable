import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.core.config import get_settings

def verify_etl_generation():
    settings = get_settings()
    engine = create_engine(settings.POSTGRES_CONNECTION_STRING)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 1. Find an active subcategory with mapping
        query = text("SELECT id, nombre, categoria_id FROM mapeo_subcategorias WHERE is_active = true AND tabla_origen IS NOT NULL LIMIT 1")
        sub = session.execute(query).fetchone()
        
        if not sub:
            print("No active subcategory found for testing.")
            return

        sub_id = sub[0]
        print(f"Testing with subcategory: {sub[1]} (id={sub_id})")

        # 2. Check if cf_diariol has data for this subcategory
        cols_query = text("SELECT column_name FROM information_schema.columns WHERE table_name = 'cf_diariol'")
        cols = [r[0] for r in session.execute(cols_query).fetchall()]
        
        if not cols:
            print("cf_diariol table not found in information_schema.")
            return

        check_cols = ["cper", "cmes", "ccodcue", "ndebe", "nhaber", "ccodmon", "subcategoria_id"]
        existing_check = [c for c in check_cols if c in cols]
        
        print(f"Checking columns: {existing_check}")

        data_query = text(f"SELECT {', '.join(existing_check)} FROM cf_diariol WHERE subcategoria_id = :sub_key LIMIT 5")
        results = session.execute(data_query, {"sub_key": sub_id}).fetchall()
        
        if not results:
            print(f"No records found in cf_diariol for subcategory {sub_id}. You may need to run Step 2 from the UI first.")
        else:
            print(f"Found {len(results)} records. Checking for nulls in standard fields:")
            for row in results:
                row_dict = dict(zip(existing_check, row))
                print(f"Row: {row_dict}")
                
                # Validation logic: standard fields should NOT be None if they were correctly mapped
                # (Assuming the subcategory has a basic mapping for these fields)
                null_fields = [k for k, v in row_dict.items() if v is None and k != "subcategoria_id"]
                if null_fields:
                    print(f"  WARNING: Null values found in: {null_fields}")
                else:
                    print("  SUCCESS: Essential fields populated.")

    except Exception as e:
        print(f"Error during verification: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    verify_etl_generation()
