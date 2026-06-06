import sys
import os
import pandas as pd
from sqlalchemy import create_engine, text

os.environ["POSTGRES_CONNECTION_STRING"] = "postgresql://postgres:postgres@localhost:5434/migconta_db"

def main():
    engine = create_engine(os.environ["POSTGRES_CONNECTION_STRING"])
    with engine.connect() as conn:
        res = conn.execute(text("SELECT id, company_id, subcategoria_id, idcontrol, estado FROM cf_diariol WHERE idcontrol = '359'"))
        rows = res.fetchall()
        if not rows:
            print("No records with idcontrol = '359' found in cf_diariol.")
        for row in rows:
            print(f"cf_diariol -> id: {row[0]}, company_id: {row[1]}, subcategoria_id: {row[2]}, idcontrol: {row[3]}, estado: {row[4]}")

if __name__ == "__main__":
    main()
