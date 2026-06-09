import sys
import os
from sqlalchemy import create_engine, text

# Database configuration
db_uri = "postgresql://postgres:postgres@localhost:5434/migconta_db"
engine = create_engine(db_uri)

def inspect_sub(sub_id):
    with engine.connect() as conn:
        res = conn.execute(text("SELECT id, nombre, col_origen_periodo, col_origen_mes, asiento_inicial, control_column_origen, filter_rules FROM mapeo_subcategorias WHERE id = :id"), {"id": sub_id})
        row = res.fetchone()
        if not row:
            print(f"Subcategory {sub_id} not found.")
            return
        print(f"--- Subcategory {sub_id} ---")
        print(f"Name: {row[1]}")
        print(f"Col Origen Periodo: {row[2]}")
        print(f"Col Origen Mes: {row[3]}")
        print(f"Asiento Inicial: {row[4]}")
        print(f"Control Column: {row[5]}")
        print(f"Filter Rules: {row[6]}")

inspect_sub(52)
inspect_sub(63)
