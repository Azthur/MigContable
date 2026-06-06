import os
from sqlalchemy import create_engine, text

os.environ["POSTGRES_CONNECTION_STRING"] = "postgresql://postgres:postgres@localhost:5434/migconta_db"

def main():
    engine = create_engine(os.environ["POSTGRES_CONNECTION_STRING"])
    with engine.connect() as conn:
        res = conn.execute(text("SELECT \"Id\", idcontrol, company_id, \"CuentaContable\", \"C_mes\", \"C_periodo\" FROM cntfacturadet WHERE idcontrol IN ('334', '359')"))
        for row in res:
            print(f"Id: {row[0]} | idcontrol: {row[1]} | company_id: {row[2]} | CuentaContable: {row[3]} | C_mes: {row[4]} | C_periodo: {row[5]}")

if __name__ == "__main__":
    main()
