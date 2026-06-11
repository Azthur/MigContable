import os
from sqlalchemy import create_engine, text

# Try to find postgres connection string
# Let's check the local docker environment or local postgres port.
# The previous script had: postgresql://postgres:postgres@localhost:5434/migconta_db
# Let's run a query to find the actual active database.

db_url = "postgresql://postgres:postgres@localhost:5434/migconta_db"

def main():
    engine = create_engine(db_url)
    with engine.connect() as conn:
        print("--- COMPANIES ---")
        companies = conn.execute(text("SELECT id, name FROM company")).mappings().all()
        for c in companies:
            print(dict(c))
            
        print("\n--- SUBCATEGORIES FOR 'BOTICA MAGISTRAL' ---")
        subcats = conn.execute(text("""
            SELECT s.id, s.nombre, s.tabla_destino_cabecera, s.tabla_destino_detalle 
            FROM mapeo_subcategoria s
            JOIN mapeo_categoria c ON s.categoria_id = c.id
            WHERE c.company_id = 1
        """)).mappings().all()
        for s in subcats:
            print(dict(s))

if __name__ == "__main__":
    main()
