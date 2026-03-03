from sqlalchemy import create_engine, text
import json
from backend.app.core.config import get_settings

def setup():
    settings = get_settings()
    engine = create_engine(settings.POSTGRES_CONNECTION_STRING)
    with engine.begin() as conn:
        # Get current mapping of line 5
        line = conn.execute(text("SELECT mapeo_detalle FROM mapeo_lineas_asiento WHERE id = 5")).fetchone()
        if not line:
            print("Line 5 not found!")
            return
            
        mapping = line[0] or {}
        # Add our test fields
        mapping["ccodsu"] = '" "' # Literal space
        mapping["valida_sunat"] = '" "' # Should be cast to 0 for numeric field
        mapping["crvieap"] = "'TEST_DYNAMIC'" # Fixed string
        
        # Update line 5
        conn.execute(text("UPDATE mapeo_lineas_asiento SET mapeo_detalle = :m WHERE id = 5"), {"m": json.dumps(mapping)})
        print("Updated line 5 with test mappings.")

if __name__ == "__main__":
    setup()
