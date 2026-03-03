import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.core.database import DestSessionLocal
from sqlalchemy import text

def add_column():
    db = DestSessionLocal()
    try:
        print("Adding column condicion_aplicacion to mapeo_lineas_asiento...")
        db.execute(text("ALTER TABLE mapeo_lineas_asiento ADD COLUMN condicion_aplicacion VARCHAR(500) NULL;"))
        db.commit()
        print("Column added successfully!")
    except Exception as e:
        if "already exists" in str(e) or "duplicate column" in str(e) or "ya existe" in str(e):
            print("Column already exists. Skipping.")
        else:
            print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    add_column()
