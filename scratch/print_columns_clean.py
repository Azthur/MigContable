import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, Table, MetaData
from backend.app.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.POSTGRES_CONNECTION_STRING, echo=False)

metadata = MetaData()
try:
    cf_diario = Table("cf_diario", metadata, autoload_with=engine)
    print("Columns in cf_diario:")
    print([c.name for c in cf_diario.columns])
except Exception as e:
    print(f"Error reading cf_diario: {e}")

try:
    cf_diariol = Table("cf_diariol", metadata, autoload_with=engine)
    print("\nColumns in cf_diariol:")
    print([c.name for c in cf_diariol.columns])
except Exception as e:
    print(f"Error reading cf_diariol: {e}")
