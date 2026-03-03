from sqlalchemy import create_engine, text
from backend.app.core.config import get_settings

def fix_schema_comprehensive():
    settings = get_settings()
    engine = create_engine(settings.POSTGRES_CONNECTION_STRING)
    with engine.connect() as conn:
        try:
            # Find all character(1) columns in cf_diario and cf_diariol
            for table in ["cf_diario", "cf_diariol"]:
                query = text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = '{table}' 
                    AND data_type = 'character' AND character_maximum_length = 1
                """)
                cols = [r[0] for r in conn.execute(query).fetchall()]
                
                for col in cols:
                    try:
                        conn.execute(text(f"ALTER TABLE {table} ALTER COLUMN {col} TYPE character varying(100)"))
                        print(f"Altered {table}.{col} to character varying(100)")
                    except Exception as e:
                        print(f"Error altering {table}.{col}: {e}")

            conn.commit()
            print("Comprehensive schema update complete.")
        except Exception as e:
            print(f"Global Error: {e}")

if __name__ == "__main__":
    fix_schema_comprehensive()
