import os
from sqlalchemy import create_engine, text

os.environ["POSTGRES_CONNECTION_STRING"] = "postgresql://postgres:postgres@localhost:5434/migconta_db"

def main():
    engine = create_engine(os.environ["POSTGRES_CONNECTION_STRING"])
    with engine.connect() as conn:
        res = conn.execute(text("SELECT * FROM cntfacturadet WHERE \"Id\" = 413")).mappings().first()
        for k, v in res.items():
            if v is not None and v != "":
                print(f"  {k}: {repr(v)}")

if __name__ == "__main__":
    main()
