import sys
import os
import pandas as pd
from sqlalchemy import create_engine, text

os.environ["POSTGRES_CONNECTION_STRING"] = "postgresql://postgres:postgres@localhost:5434/migconta_db"

def main():
    engine = create_engine(os.environ["POSTGRES_CONNECTION_STRING"])
    with engine.connect() as conn:
        # Check column names of cntfacturadet
        print("Columns in cntfacturadet:")
        res = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'cntfacturadet'"))
        for col in res:
            print(f"  {col[0]}: {col[1]}")

        # Check total count and count by company_id
        print("\nCounts in cntfacturadet by company_id:")
        res_count = conn.execute(text("SELECT company_id, count(*) FROM cntfacturadet GROUP BY company_id"))
        for row in res_count:
            print(f"  Company {row[0]}: {row[1]}")

        # Check if there is an idcontrol column and sample values
        print("\nSample idcontrol values from cntfacturadet:")
        res_sample = conn.execute(text("SELECT idcontrol, company_id, count(*) FROM cntfacturadet GROUP BY idcontrol, company_id LIMIT 10"))
        for row in res_sample:
            print(f"  idcontrol: {row[0]}, company_id: {row[1]}, count: {row[2]}")

        # Specifically, check idcontrol '359' or similar
        print("\nSearching for idcontrol = '359':")
        res_359 = conn.execute(text("SELECT \"Id\", idcontrol, company_id, \"C_mes\", \"C_periodo\" FROM cntfacturadet WHERE idcontrol = '359'"))
        for row in res_359:
            print(f"  id: {row[0]}, idcontrol: {row[1]}, company_id: {row[2]}, C_mes: {row[3]}, C_periodo: {row[4]}")

if __name__ == "__main__":
    main()
