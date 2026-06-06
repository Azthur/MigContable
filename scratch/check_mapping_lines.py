import os
from sqlalchemy import create_engine, text

os.environ["POSTGRES_CONNECTION_STRING"] = "postgresql://postgres:postgres@localhost:5434/migconta_db"

def main():
    engine = create_engine(os.environ["POSTGRES_CONNECTION_STRING"])
    with engine.connect() as conn:
        print("Subcategory 63 mapping header and details:")
        # Check subcategory main columns
        res_sub = conn.execute(text("SELECT id, nombre, tabla_origen, clave_asiento, filter_rules, generate_headers, generate_details FROM mapeo_subcategorias WHERE id = 63")).mappings().first()
        print(dict(res_sub))
        
        # Check mapping lines
        res_lines = conn.execute(text("SELECT id, orden, nombre_linea, condicion_aplicacion, mapeo_detalle, nivel FROM mapeo_lineas_asiento WHERE subcategoria_id = 63 ORDER BY orden")).mappings().all()
        print(f"\nFound {len(res_lines)} lines:")
        for idx, line in enumerate(res_lines):
            print(f"\nLine {idx+1}: ID={line['id']}, Name='{line['nombre_linea']}', Nivel={line['nivel']}")
            print(f"  Condition: {line['condicion_aplicacion']}")
            print(f"  Mapping Detail: {line['mapeo_detalle']}")

if __name__ == "__main__":
    main()
