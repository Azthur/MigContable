from sqlalchemy import create_engine, text
from backend.app.core.config import get_settings

def check_data():
    settings = get_settings()
    engine = create_engine(settings.POSTGRES_CONNECTION_STRING)
    with engine.connect() as conn:
        try:
            count = conn.execute(text("SELECT count(*) FROM ventas")).scalar()
            print(f"Table 'ventas' has {count} rows.")
            if count > 0:
                sample = conn.execute(text("SELECT * FROM ventas LIMIT 1")).fetchone()
                print(f"Sample row: {sample}")
        except Exception as e:
            print(f"Error checking 'ventas': {e}")

if __name__ == "__main__":
    check_data()
