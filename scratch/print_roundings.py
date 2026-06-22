import os
from sqlalchemy import create_engine, text

os.environ["POSTGRES_CONNECTION_STRING"] = "postgresql://postgres:postgres@localhost:5434/migconta_db"

def main():
    engine = create_engine(os.environ["POSTGRES_CONNECTION_STRING"])
    with engine.connect() as conn:
        print("--- Subcategory 76 Rounding Config ---")
        sub = conn.execute(text("SELECT id, pares_redondeo FROM mapeo_subcategorias WHERE id = 76")).mappings().first()
        print("pares_redondeo:", sub['pares_redondeo'])
        
        print("\n--- Lines aplica_ajuste_redondeo ---")
        lines = conn.execute(text("SELECT id, nombre_linea, aplica_ajuste_redondeo FROM mapeo_lineas_asiento WHERE subcategoria_id = 76 ORDER BY orden")).mappings().all()
        for l in lines:
            print(dict(l))

if __name__ == "__main__":
    main()
