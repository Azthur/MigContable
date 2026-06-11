import os
import sys
# Add parent dir to PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect
from backend.app.core.database import dest_engine

inspector = inspect(dest_engine)
cols = [c['name'] for c in inspector.get_columns("ccbrrdoc")]
print("Columns in ccbrrdoc:")
print(cols)
print("Is 'estado' in ccbrrdoc columns?", "estado" in cols)
print("Is 'C_estado' in ccbrrdoc columns?", "C_estado" in cols)
print("Is 'C_ESTADO' in ccbrrdoc columns?", "C_ESTADO" in cols)
