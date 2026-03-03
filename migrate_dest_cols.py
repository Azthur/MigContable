import sys
import os

# Load env from .env file
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.database import dest_engine
from sqlalchemy import text

sqls = [
    "ALTER TABLE mapeo_subcategorias ADD COLUMN IF NOT EXISTS tabla_destino_detalle VARCHAR(200)",
    "ALTER TABLE mapeo_subcategorias ADD COLUMN IF NOT EXISTS tabla_destino_cabecera VARCHAR(200)",
    "ALTER TABLE mapeo_subcategorias ADD COLUMN IF NOT EXISTS schema_destino VARCHAR(100) DEFAULT 'public'",
]

with dest_engine.connect() as conn:
    for sql in sqls:
        try:
            conn.execute(text(sql))
            print("OK:", sql[:70])
        except Exception as e:
            print("ERROR:", sql[:50], "->", e)
    conn.commit()

print("Migration complete")
