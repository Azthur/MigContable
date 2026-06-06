import os
from sqlalchemy import create_engine, text

os.environ["POSTGRES_CONNECTION_STRING"] = "postgresql://postgres:postgres@localhost:5434/migconta_db"

def main():
    engine = create_engine(os.environ["POSTGRES_CONNECTION_STRING"])
    with engine.connect() as conn:
        res = conn.execute(text("""
            SELECT s.id, s.nombre, s.tabla_origen, c.company_id 
            FROM mapeo_subcategorias s
            JOIN mapeo_categorias c ON s.categoria_id = c.id
            WHERE s.id IN (46, 63)
        """))
        for row in res:
            print(f"Subcategory {row[0]}: Name: {row[1]}, Tabla Origen: {row[2]}, Company ID: {row[3]}")

if __name__ == "__main__":
    main()
