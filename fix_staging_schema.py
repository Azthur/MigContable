from sqlalchemy import create_engine, text
from backend.app.core.config import get_settings

def fix_schema():
    settings = get_settings()
    engine = create_engine(settings.POSTGRES_CONNECTION_STRING)
    with engine.connect() as conn:
        try:
            # Fix cf_diario
            conn.execute(text("ALTER TABLE cf_diario ALTER COLUMN cper TYPE character varying(4)"))
            conn.execute(text("ALTER TABLE cf_diario ALTER COLUMN cmes TYPE character varying(2)"))
            conn.execute(text("ALTER TABLE cf_diario ALTER COLUMN ccodori TYPE character varying(10)"))
            conn.execute(text("ALTER TABLE cf_diario ALTER COLUMN cmoneda TYPE character varying(10)"))
            conn.execute(text("ALTER TABLE cf_diario ALTER COLUMN ccodsu TYPE character varying(10)"))
            conn.execute(text("ALTER TABLE cf_diario ALTER COLUMN ccodusu TYPE character varying(50)"))
            conn.execute(text("ALTER TABLE cf_diario ALTER COLUMN ccodbas TYPE character varying(10)"))
            
            # Fix cf_diariol
            conn.execute(text("ALTER TABLE cf_diariol ALTER COLUMN cper TYPE character varying(4)"))
            conn.execute(text("ALTER TABLE cf_diariol ALTER COLUMN cmes TYPE character varying(2)"))
            conn.execute(text("ALTER TABLE cf_diariol ALTER COLUMN ccodori TYPE character varying(10)"))
            conn.execute(text("ALTER TABLE cf_diariol ALTER COLUMN cmoneda TYPE character varying(10)"))
            conn.execute(text("ALTER TABLE cf_diariol ALTER COLUMN ccodsu TYPE character varying(10)"))

            conn.commit()
            print("Schema fixed: cper, cmes and other char(1) columns expanded.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    fix_schema()
