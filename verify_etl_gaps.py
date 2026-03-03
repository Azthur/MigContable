from sqlalchemy import create_engine, text
from backend.app.core.config import get_settings
import json

def verify_all():
    settings = get_settings()
    engine = create_engine(settings.POSTGRES_CONNECTION_STRING)
    with engine.connect() as conn:
        # Check if columns exist in cf_diariol
        query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'cf_diariol'
        """)
        cols = [r[0] for r in conn.execute(query).fetchall()]
        print("--- SCHEMA CHECK: cf_diariol ---")
        targets = ['cper', 'cmes', 'ccodori', 'ccodcue', 'ccodsu', 'ndebe', 'nhaber', 'nasiento', 'nidlin']
        for t in targets:
            print(f"Column '{t}': {'EXISTS' if t in cols else 'MISSING'}")
        
        # Check sub 4 config
        print("\n--- SUBCATEGORIA 4 CONFIG ---")
        sub = conn.execute(text("SELECT id, nombre, tabla_destino_detalle, col_destino_nasiento, col_destino_nidlin FROM mapeo_subcategorias WHERE id = 4")).mappings().first()
        print(json.dumps(dict(sub), indent=2))
        
        # Check mapping line 1
        print("\n--- MAPPING LINE 1 DETAIL ---")
        linea = conn.execute(text("SELECT id, nivel, mapeo_detalle FROM mapeo_lineas_asiento WHERE subcategoria_id = 4 ORDER BY id LIMIT 1")).mappings().first()
        if linea:
            print(f"Level: {linea['nivel']}")
            print("Mapping Keys (first 20):", list(linea['mapeo_detalle'].keys())[:20])
            for k in targets:
                if k in linea['mapeo_detalle']:
                    print(f"Mapping for '{k}': {linea['mapeo_detalle'][k]}")
                else:
                    print(f"Mapping for '{k}': NOT CONFIGURED")

if __name__ == "__main__":
    verify_all()
