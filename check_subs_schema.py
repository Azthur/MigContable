from sqlalchemy import create_engine, text
from backend.app.core.config import get_settings

def check_schema():
    settings = get_settings()
    engine = create_engine(settings.POSTGRES_CONNECTION_STRING)
    with engine.connect() as conn:
        query = text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'mapeo_subcategorias'
        """)
        cols = conn.execute(query).fetchall()
        print("Columns in mapeo_subcategorias:")
        for c in cols:
            print(f" - {c[0]}: {c[1]}")

if __name__ == "__main__":
    check_schema()
