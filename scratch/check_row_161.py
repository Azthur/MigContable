import os
from sqlalchemy import create_engine, text

os.environ["POSTGRES_CONNECTION_STRING"] = "postgresql://postgres:postgres@localhost:5434/migconta_db"

def main():
    engine = create_engine(os.environ["POSTGRES_CONNECTION_STRING"])
    with engine.connect() as conn:
        res = conn.execute(text("""
            SELECT "Id", idcontrol, company_id, "CodCia", "C_TipoDoc", "CuentaContable", "C_mes", "C_periodo" 
            FROM cntfacturadet 
            WHERE "C_Numero_F" = '00000000000001035690' OR "C_Numero" = '1035690'
        """)).mappings().all()
        for r in res:
            print(dict(r))

if __name__ == "__main__":
    main()
