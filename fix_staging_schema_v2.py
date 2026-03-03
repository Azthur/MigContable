from sqlalchemy import create_engine, text
from backend.app.core.config import get_settings

def fix_schema():
    settings = get_settings()
    engine = create_engine(settings.POSTGRES_CONNECTION_STRING)
    with engine.connect() as conn:
        def alter_if_exists(table, col, new_type):
            try:
                # Check if column exists
                check = conn.execute(text(f"""
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = '{table}' AND column_name = '{col}'
                """)).fetchone()
                if check:
                    conn.execute(text(f"ALTER TABLE {table} ALTER COLUMN {col} TYPE {new_type}"))
                    print(f"Altered {table}.{col} to {new_type}")
            except Exception as e:
                print(f"Error altering {table}.{col}: {e}")

        alter_if_exists("cf_diario", "cper", "character varying(4)")
        alter_if_exists("cf_diario", "cmes", "character varying(2)")
        alter_if_exists("cf_diario", "ccodori", "character varying(10)")
        alter_if_exists("cf_diario", "cmoneda", "character varying(10)")
        alter_if_exists("cf_diario", "ccodsu", "character varying(10)")
        alter_if_exists("cf_diario", "ccodusu", "character varying(50)")
        alter_if_exists("cf_diario", "ccodbas", "character varying(10)")
        
        alter_if_exists("cf_diariol", "cper", "character varying(4)")
        alter_if_exists("cf_diariol", "cmes", "character varying(2)")
        alter_if_exists("cf_diariol", "ccodori", "character varying(10)")
        alter_if_exists("cf_diariol", "cmoneda", "character varying(10)")
        alter_if_exists("cf_diariol", "ccodsu", "character varying(10)")

        conn.commit()
        print("Schema update complete.")

if __name__ == "__main__":
    fix_schema()
