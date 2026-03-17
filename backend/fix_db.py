from backend.app.core.database import dest_engine
from sqlalchemy import text

with dest_engine.connect() as conn:
    conn.execute(text('ALTER TABLE mapeo_subcategorias ADD COLUMN IF NOT EXISTS asiento_inicial INTEGER'))
    conn.commit()
print('Column added successfully')
