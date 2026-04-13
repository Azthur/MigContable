import sys, os
sys.path.append(os.getcwd())
import pandas as pd
from backend.app.api.endpoints.etl import ConnectionManager
from backend.app.models.models import SourceConnection
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
import sqlalchemy as sa
from backend.app.core.database import DestSessionLocal

db = DestSessionLocal()
conn_data = db.query(SourceConnection).filter_by(id=4).first()
if conn_data:
    src_data = {
        "host": conn_data.host, "port": conn_data.port,
        "database_name": conn_data.database_name,
        "username": conn_data.username, "password": conn_data.password,
        "driver": conn_data.driver, "db_type": conn_data.db_type
    }
    src_engine = ConnectionManager.get_source_engine(src_data)
    with src_engine.connect() as conn:
        df = pd.read_sql("SELECT TOP 5 CodCia, coddoc, nrodoc FROM [dbo].[VtaRItem] WHERE CodCia = '005'", conn)
        print(df.to_string())
