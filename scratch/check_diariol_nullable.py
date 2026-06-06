import os
from sqlalchemy import create_engine, text

os.environ["POSTGRES_CONNECTION_STRING"] = "postgresql://postgres:postgres@localhost:5434/migconta_db"

def main():
    engine = create_engine(os.environ["POSTGRES_CONNECTION_STRING"])
    with engine.connect() as conn:
        res = conn.execute(text("""
            SELECT column_name, is_nullable, data_type, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'cf_diariol'
        """)).mappings().all()
        
        print("Columns in cf_diariol with constraints:")
        for r in res:
            name = r['column_name']
            nullable = r['is_nullable']
            dtype = r['data_type']
            default = r['column_default']
            # Highlight NOT NULL columns
            if nullable == 'NO':
                print(f"  {name}: {dtype} | Nullable: {nullable} | Default: {default}")

if __name__ == "__main__":
    main()
