#!/usr/bin/env python3
"""Script para revisar columnas calculadas de subcategorías 81 y 116."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def check_computed_columns():
    db = next(get_dest_db())
    
    try:
        print("=== COLUMNAS CALCULADAS DE SUBCATEGORÍAS 81 Y 116 ===")
        
        # Primero necesito encontrar los table_selection_id para estas subcategorías
        result = db.execute(text("""
            SELECT ts.id, ts.table_name, s.id as subcategoria_id, s.nombre
            FROM table_selections ts
            JOIN mapeo_subcategorias s ON ts.table_name = s.tabla_origen
            WHERE s.id IN (81, 116)
        """))
        
        selection_ids = []
        for row in result:
            print(f"\nTable Selection ID: {row[0]} | Tabla: {row[1]} | Subcategoría: {row[2]} ({row[3]})")
            selection_ids.append(row[0])
        
        if not selection_ids:
            print("No se encontraron table_selections para estas subcategorías")
            return
        
        # Revisar columnas calculadas para cada selection_id
        for sel_id in selection_ids:
            print(f"\n--- Columnas calculadas para selection_id {sel_id} ---")
            result = db.execute(text("""
                SELECT new_column_name, source_column, condition_value, result_value, default_value, priority, is_active
                FROM computed_column_rules
                WHERE table_selection_id = :sel_id
                ORDER BY priority
            """), {"sel_id": sel_id})
            
            has_rules = False
            for row in result:
                has_rules = True
                print(f"  {row[0]} <- {row[1]}")
                print(f"    Condición: {row[2]}")
                print(f"    Resultado: {row[3]}")
                print(f"    Default: {row[4]}")
                print(f"    Prioridad: {row[5]} | Activo: {row[6]}")
                print()
            
            if not has_rules:
                print("  No hay reglas de columnas calculadas")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_computed_columns()
