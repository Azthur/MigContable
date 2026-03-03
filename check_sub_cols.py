from sqlalchemy import create_engine, text
from backend.app.core.config import get_settings
import json

def check_sub():
    settings = get_settings()
    engine = create_engine(settings.POSTGRES_CONNECTION_STRING)
    with engine.connect() as conn:
        try:
            res = conn.execute(text("SELECT id, nombre, col_destino_nasiento, col_destino_nidlin FROM mapeo_subcategorias WHERE id = 4")).fetchone()
            print(f"Sub 4: {res}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    check_sub()
