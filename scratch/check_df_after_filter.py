import sys
import os
import pandas as pd
from sqlalchemy import create_engine, text

os.environ["POSTGRES_CONNECTION_STRING"] = "postgresql://postgres:postgres@localhost:5434/migconta_db"

from backend.app.core.database import DestSessionLocal
from backend.app.models.models import MapeoSubcategoria
from backend.app.core.database import dest_engine

def main():
    db = DestSessionLocal()
    try:
        sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == 63).first()
        if not sub:
            print("Subcategory 63 not found!")
            return
            
        print("Reading raw source data...")
        with dest_engine.connect() as conn:
            # Query the source table with active filters: period 2026, mes 06
            query = 'SELECT * FROM "cntfacturadet" WHERE "company_id" = 4 AND "C_periodo" = \'2026\' AND "C_mes" = \'06\''
            df = pd.read_sql(query, conn)
            
        print("Raw records matching 2026-06:", len(df))
        if df.empty:
            return
            
        print("Columns in df:", list(df.columns))
        print("Sample values:")
        for idx, row in df.iterrows():
            print(f"Row {idx}: idcontrol={row.get('idcontrol')}, CodCia={row.get('CodCia')}, C_TipoDoc={row.get('C_TipoDoc')}, FacturaCabId={row.get('FacturaCabId')}")
            
    finally:
        db.close()

if __name__ == "__main__":
    main()
