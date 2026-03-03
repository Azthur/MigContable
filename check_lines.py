from sqlalchemy import create_engine, text
import json
from backend.app.core.config import get_settings

def check():
    settings = get_settings()
    engine = create_engine(settings.POSTGRES_CONNECTION_STRING)
    with engine.connect() as conn:
        print("--- SUBCATEGORIES ---")
        subs = conn.execute(text("SELECT id, nombre FROM mapeo_subcategorias")).fetchall()
        for s in subs:
            print(f"ID: {s[0]} | Name: {s[1]}")
            
        print("\n--- MAPPING LINES ---")
        lines = conn.execute(text("SELECT id, subcategoria_id, nombre_linea FROM mapeo_lineas_asiento")).fetchall()
        for l in lines:
            print(f"Line ID: {l[0]} | Subcat ID: {l[1]} | Name: {l[2]}")

if __name__ == "__main__":
    check()
