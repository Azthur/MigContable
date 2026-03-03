from sqlalchemy import create_engine, text
from backend.app.core.config import get_settings

def check_full_schema():
    settings = get_settings()
    engine = create_engine(settings.POSTGRES_CONNECTION_STRING)
    with engine.connect() as conn:
        try:
            query = text("""
                SELECT column_name, data_type, character_maximum_length 
                FROM information_schema.columns 
                WHERE table_name = 'cf_diario'
            """)
            result = conn.execute(query).fetchall()
            print("cf_diario Full Schema:")
            for row in result:
                print(f" - {row[0]}: {row[1]} (len={row[2]})")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    check_full_schema()
