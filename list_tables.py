from sqlalchemy import create_engine, text
from backend.app.core.config import get_settings

def list_tables():
    settings = get_settings()
    engine = create_engine(settings.POSTGRES_CONNECTION_STRING)
    with engine.connect() as conn:
        try:
            # Query information_schema for tables in 'public' or other non-system schemas
            query = text("""
                SELECT table_schema, table_name 
                FROM information_schema.tables 
                WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
                ORDER BY table_schema, table_name
            """)
            result = conn.execute(query).fetchall()
            print("Tables found in DB:")
            for schema, name in result:
                print(f" - {schema}.{name}")
        except Exception as e:
            print(f"Error listing tables: {e}")

if __name__ == "__main__":
    list_tables()
