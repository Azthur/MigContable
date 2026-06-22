import os
from sqlalchemy import create_engine, text

os.environ["POSTGRES_CONNECTION_STRING"] = "postgresql://postgres:postgres@localhost:5434/migconta_db"

def main():
    engine = create_engine(os.environ["POSTGRES_CONNECTION_STRING"])
    with engine.connect() as conn:
        res_lines = conn.execute(text("SELECT id, nombre_linea, condicion_aplicacion, mapeo_detalle, nivel FROM mapeo_lineas_asiento WHERE subcategoria_id = 76 ORDER BY orden")).mappings().all()
        for idx, line in enumerate(res_lines):
            print(f"\nLine {idx+1}: ID={line['id']}, Name='{line['nombre_linea']}', Nivel={line['nivel']}")
            print(f"  Condition: {repr(line['condicion_aplicacion'])}")
            print("  Mapeo Detalle:")
            detail = line['mapeo_detalle']
            if isinstance(detail, dict):
                for k, v in detail.items():
                    # Only print non-zero/non-empty mapping fields to see the relevant ones
                    if v not in ('0', '""', '" "', '"                   "', '"  "', '"   "', '"    "', '', None):
                        print(f"    {k}: {repr(v)}")
            else:
                print(f"    {detail}")

if __name__ == "__main__":
    main()
