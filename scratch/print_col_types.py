import os
import sys
from sqlalchemy import create_engine, MetaData, Table

os.environ["POSTGRES_CONNECTION_STRING"] = "postgresql://postgres:postgres@localhost:5434/migconta_db"

def main():
    engine = create_engine(os.environ["POSTGRES_CONNECTION_STRING"])
    metadata = MetaData()
    DetTable = Table("cf_diariol", metadata, autoload_with=engine)
    
    col = DetTable.c.get("ndebe")
    print(f"Column 'ndebe':")
    print(f"  Type object: {col.type}")
    print(f"  Type class: {col.type.__class__}")
    
    from sqlalchemy import Numeric, Float, Integer, Date
    print(f"  isinstance(type, Numeric): {isinstance(col.type, Numeric)}")
    print(f"  isinstance(type, Float): {isinstance(col.type, Float)}")

if __name__ == "__main__":
    main()
