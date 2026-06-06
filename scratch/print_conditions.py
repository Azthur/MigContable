import os
from sqlalchemy import create_engine, text

os.environ["POSTGRES_CONNECTION_STRING"] = "postgresql://postgres:postgres@localhost:5434/migconta_db"

def main():
    engine = create_engine(os.environ["POSTGRES_CONNECTION_STRING"])
    with engine.connect() as conn:
        res = conn.execute(text("""
            SELECT id, orden, nombre_linea, condicion_aplicacion, nivel 
            FROM mapeo_lineas_asiento 
            WHERE subcategoria_id = 63 
            ORDER BY orden
        """)).mappings().all()
        print(f"Subcategory 63 mapping lines:")
        for idx, line in enumerate(res):
            print(f"Line {line['orden']}: Name='{line['nombre_linea']}', Nivel={line['nivel']}, Condition='{line['condicion_aplicacion']}'")

if __name__ == "__main__":
    main()
