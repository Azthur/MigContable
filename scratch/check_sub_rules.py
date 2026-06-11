from backend.app.core.database import dest_engine
from sqlalchemy import text
import json

with dest_engine.connect() as conn:
    row = conn.execute(text("SELECT id, nombre, filter_rules, last_generated_control_value, control_column_origen FROM mapeo_subcategorias WHERE id = 35")).fetchone()
    print("ID:", row[0])
    print("Nombre:", row[1])
    print("Filter Rules:", json.loads(json.dumps(row[2])) if row[2] else None)
    print("Last Generated Control Value:", row[3])
    print("Control Column Origen:", row[4])
