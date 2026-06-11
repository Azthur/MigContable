import sys
sys.path.append('c:/SistemaMigConta')
from backend.app.core.database import dest_engine
from sqlalchemy import inspect

insp = inspect(dest_engine)
columns = [c['name'] for c in insp.get_columns("cg_entitrib")]
print("cg_entitrib columns:", columns)
