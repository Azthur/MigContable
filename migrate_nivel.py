import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.core.database import dest_engine
from sqlalchemy import text

try:
    with dest_engine.begin() as conn:
        conn.execute(text("ALTER TABLE mapeo_lineas_asiento ADD COLUMN IF NOT EXISTS nivel VARCHAR(20) DEFAULT 'DETALLE'"))
    print("Migración completada exitosamente.")
except Exception as e:
    print(f"Error en la migración: {e}")
