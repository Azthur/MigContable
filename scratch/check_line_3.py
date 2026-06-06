import os
from sqlalchemy import create_engine, text

os.environ["POSTGRES_CONNECTION_STRING"] = "postgresql://postgres:postgres@localhost:5434/migconta_db"

def main():
    engine = create_engine(os.environ["POSTGRES_CONNECTION_STRING"])
    with engine.connect() as conn:
        res = conn.execute(text("SELECT id, orden, nombre_linea, condicion_aplicacion, mapeo_detalle, nivel FROM mapeo_lineas_asiento WHERE subcategoria_id = 63 AND orden IN (3, 4)")).mappings().all()
        for r in res:
            print(f"Line {r['orden']}: Name='{r['nombre_linea']}', Nivel={r['nivel']}")
            print(f"  Mapping Detail: {r['mapeo_detalle']}")

if __name__ == "__main__":
    main()
