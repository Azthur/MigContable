from sqlalchemy import create_engine, text
from backend.app.core.config import get_settings
import json

def check_schema_and_mapping():
    settings = get_settings()
    engine = create_engine(settings.POSTGRES_CONNECTION_STRING)
    with engine.connect() as conn:
        # Check columns
        query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'cf_diariol'
        """)
        cols = [r[0] for r in conn.execute(query).fetchall()]
        print("Columns in cf_diariol:")
        target_cols = ['cper', 'cmes', 'ccodori', 'ccodcue', 'ccodsu', 'ndebe', 'nhaber']
        for tc in target_cols:
            print(f" - {tc}: {'EXISTS' if tc in cols else 'MISSING'}")
        
        # Check mapping for sub 4
        res = conn.execute(text("SELECT mapeo_detalle FROM mapeo_lineas_asiento WHERE subcategoria_id = 4")).fetchall()
        print(f"\nFound {len(res)} mapping lines for sub 4.")
        for i, r in enumerate(res):
            print(f"Line {i+1} mapping: {json.dumps(r[0], indent=2)}")

if __name__ == "__main__":
    check_schema_and_mapping()
