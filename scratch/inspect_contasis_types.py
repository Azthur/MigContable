import sys
sys.path.append('c:/SistemaMigConta')
from backend.app.core.database import DestSessionLocal
from backend.app.models.models import FinalDestConnection
from backend.app.services.connection_manager import ConnectionManager
from sqlalchemy import text, inspect

db = DestSessionLocal()
try:
    final_conn = db.query(FinalDestConnection).filter(
        FinalDestConnection.company_id == 1,
        FinalDestConnection.is_active == True
    ).first()
    
    if final_conn:
        conn_data = {
            "host": final_conn.host, "port": final_conn.port,
            "database_name": final_conn.database_name,
            "username": final_conn.username, "password": final_conn.password
        }
        final_engine = ConnectionManager.get_dest_engine(conn_data)
        
        # Obtener tipos de columnas
        insp = inspect(final_engine)
        
        print("cf_diario columns and types:")
        for col in insp.get_columns("cf_diario"):
            if col['name'] in ['nasiento', 'nidlin', 'cper', 'cmes', 'ccodori']:
                print(f"  {col['name']}: {col['type']}")
                
        print("\ncf_diariol columns and types:")
        for col in insp.get_columns("cf_diariol"):
            if col['name'] in ['nasiento', 'nidlin', 'cper', 'cmes', 'ccodori', 'ccodcue', 'ndebe', 'nhaber']:
                print(f"  {col['name']}: {col['type']}")
finally:
    db.close()
