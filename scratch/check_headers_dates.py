import os
from sqlalchemy import create_engine, text

os.environ["POSTGRES_CONNECTION_STRING"] = "postgresql://postgres:postgres@localhost:5434/migconta_db"

def main():
    engine = create_engine(os.environ["POSTGRES_CONNECTION_STRING"])
    with engine.connect() as conn:
        res = conn.execute(text("SELECT id, created_at, lote_id, estado, nasiento FROM cf_diario WHERE company_id = 4 AND subcategoria_id = 63 ORDER BY id")).mappings().all()
        print(f"Total headers: {len(res)}")
        for idx, row in enumerate(res):
            print(f"Row {idx+1}: ID={row['id']}, Created={row['created_at']}, Lote={row['lote_id']}, Estado={row['estado']}, nasiento={row['nasiento']}")

if __name__ == "__main__":
    main()
