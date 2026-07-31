#!/usr/bin/env python3
"""Script para revisar mapeo de columnas de origen a destino."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def check_column_mappings():
    db = next(get_dest_db())
    
    try:
        print("=== MAPEO DE COLUMNAS ORIGEN -> DESTINO ===")
        
        # Revisar column_mappings para subcategorías 81 y 116
        result = db.execute(text("""
            SELECT cm.id, cm.source_column, cm.dest_column, s.id as subcategoria_id, s.nombre
            FROM column_mappings cm
            JOIN table_selections ts ON cm.table_selection_id = ts.id
            JOIN mapeo_subcategorias s ON ts.table_name = s.tabla_origen
            WHERE s.id IN (81, 116)
            ORDER BY s.id, cm.source_column
        """))
        
        found = False
        for row in result:
            found = True
            print(f"\nSubcategoría {row[3]} ({row[4]}):")
            print(f"  {row[1]} -> {row[2]}")
        
        if not found:
            print("No se encontraron column_mappings para estas subcategorías")
            
            # Intentar buscar table_selections directamente
            print("\nBuscando table_selections para estas subcategorías...")
            result = db.execute(text("""
                SELECT ts.id, ts.table_name, s.id as subcategoria_id, s.nombre
                FROM table_selections ts
                JOIN mapeo_subcategorias s ON ts.table_name = s.tabla_origen
                WHERE s.id IN (81, 116)
            """))
            
            for row in result:
                print(f"  Table Selection ID: {row[0]} | Tabla: {row[1]} | Subcategoría: {row[2]} ({row[3]})")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_column_mappings()
