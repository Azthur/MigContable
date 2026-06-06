import os
from sqlalchemy import create_engine, text

os.environ["POSTGRES_CONNECTION_STRING"] = "postgresql://postgres:postgres@localhost:5434/migconta_db"

def main():
    engine = create_engine(os.environ["POSTGRES_CONNECTION_STRING"])
    with engine.connect() as conn:
        res = conn.execute(text("""
            SELECT id, orden, nombre_linea, condicion_aplicacion, mapeo_detalle, nivel 
            FROM mapeo_lineas_asiento 
            WHERE subcategoria_id = 63 AND orden = 1
        """)).mappings().first()
        if res:
            print("Line 1 Details:")
            print(f"  ID: {res['id']}")
            print(f"  Orden: {res['orden']}")
            print(f"  Nombre: '{res['nombre_linea']}'")
            print(f"  Nivel: {res['nivel']}")
            print(f"  Condición: '{res['condicion_aplicacion']}'")
            print(f"  Mapeo Detalle: {res['mapeo_detalle']}")
        else:
            print("Line 1 not found!")

if __name__ == "__main__":
    main()
