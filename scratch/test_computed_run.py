import sys
import os
import pandas as pd
from sqlalchemy import create_engine

# Add project root to path
sys.path.append("c:\\SistemaMigConta")

# Set up connection strings
os.environ["POSTGRES_CONNECTION_STRING"] = "postgresql://postgres:postgres@localhost:5434/migconta_db"

from backend.app.core.database import DestSessionLocal
from backend.app.models.models import ComputedColumnRule, TableSelection
from backend.app.api.endpoints.etl import __apply_computed_rules

def main():
    db = DestSessionLocal()
    try:
        company_id = 4
        table_selection_id = 58
        
        # Load computed rules
        rules = db.query(ComputedColumnRule).filter(
            ComputedColumnRule.table_selection_id == table_selection_id,
            ComputedColumnRule.is_active == True
        ).order_by(ComputedColumnRule.priority).all()
        
        print(f"Loaded {len(rules)} active rules.")
        for r in rules:
            print(f"  Rule ID {r.id}: {r.new_column_name} = {r.condition_value}")
            
        # Let's load the data from SQL Server
        import pyodbc
        conn = pyodbc.connect('DRIVER={SQL Server};SERVER=192.168.1.17\\SQL2022;DATABASE=yelave22;UID=JUBER2;PWD=PasswordSeguro123!')
        
        df = pd.read_sql('SELECT * FROM CntFacturaDet', conn)
        print("Loaded CntFacturaDet from SQL Server. Rows:", len(df))
        
        # Apply rules
        __apply_computed_rules(df, rules, db, company_id, "CntFacturaDet")
        
        print("\nColumns after applying rules:")
        print(df.columns.tolist())
        
        print("\nChecking populated values for CodCia and C_car:")
        print(df[['FacturaCabId', 'CodCia', 'C_car']].head(20))
        
        # Let's see if there are any non-empty CodCia values
        non_empty = df[df['CodCia'].astype(str).str.strip() != ""]
        print(f"\nNumber of non-empty CodCia rows: {len(non_empty)}")
        if len(non_empty) > 0:
            print(non_empty[['FacturaCabId', 'CodCia', 'C_car']].head(20))
            
    finally:
        db.close()

if __name__ == "__main__":
    main()
