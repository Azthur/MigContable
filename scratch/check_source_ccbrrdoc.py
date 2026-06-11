import os
import sys
# Add parent dir to PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from backend.app.core.database import DestSessionLocal
from backend.app.models.models import SourceConnection
from backend.app.services.connection_manager import ConnectionManager

db = DestSessionLocal()
try:
    source_conn = db.query(SourceConnection).filter(SourceConnection.company_id == 1).first()
    if not source_conn:
        print("Source connection not found")
    else:
        src_data = {
            "host": source_conn.host,
            "port": source_conn.port,
            "database_name": source_conn.database_name,
            "username": source_conn.username,
            "password": source_conn.password,
            "driver": source_conn.driver,
            "db_type": source_conn.db_type
        }
        src_engine = ConnectionManager.get_source_engine(src_data)
        
        query = "SELECT TOP 1 * FROM ccbrrdoc"
        df = pd.read_sql(query, src_engine)
        print("Columns in SQL Server ccbrrdoc:")
        print(list(df.columns))
finally:
    db.close()
