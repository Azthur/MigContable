from sqlalchemy import create_engine, text
from backend.app.core.config import get_settings

def check_mapping_config():
    settings = get_settings()
    engine = create_engine(settings.POSTGRES_CONNECTION_STRING)
    with engine.connect() as conn:
        try:
            # Check all subcategories and their tabla_origen
            query = text("SELECT id, nombre, tabla_origen FROM mapeo_subcategorias WHERE is_active = true")
            result = conn.execute(query).fetchall()
            print("Subcategories Configured:")
            for sub_id, nombre, tabla in result:
                print(f" - ID {sub_id}: {nombre} (Source Table: {tabla})")
                
                # Check mapping lines
                line_count = conn.execute(text("SELECT count(*) FROM mapeo_lineas_asiento WHERE subcategoria_id = :sid"), {"sid": sub_id}).scalar()
                print(f"   Lines: {line_count}")

            # Check if ccbrgdoc or vtaritem have data
            for t in ["ccbrgdoc", "vtaritem"]:
                c = conn.execute(text(f"SELECT count(*) FROM {t}")).scalar()
                print(f"Table '{t}' has {c} rows.")

        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    check_mapping_config()
