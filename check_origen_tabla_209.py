#!/usr/bin/env python3
"""Script para verificar de dónde se extrae C_ctabaseF."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def check_origen_tabla_209():
    db = next(get_dest_db())
    
    try:
        print("=== ORIGEN DE DATOS PARA LIBRO 209 ===")
        
        # Verificar tabla_origen en mapeo_subcategorias
        result = db.execute(text("""
            SELECT id, nombre, tabla_origen, codigo_origen
            FROM mapeo_subcategorias
            WHERE id IN (80, 81, 82, 83, 116)
        """))
        
        print("Tabla origen por subcategoría:")
        for row in result:
            print(f"  ID {row[0]} ({row[1]}): {row[2]} (código: {row[3]})")
        
        # Verificar table_selections para ver la conexión
        print("\n=== TABLE_SELECTIONS PARA LIBRO 209 ===")
        result = db.execute(text("""
            SELECT ts.id, ts.source_table_name, ts.company_id, ts.connection_id
            FROM table_selections ts
            WHERE ts.source_table_name ILIKE '%planilla%'
            ORDER BY ts.company_id
        """))
        
        for row in result:
            print(f"  ID {row[0]}: {row[1]} (company_id: {row[2]}, connection_id: {row[3]})")
        
        # Verificar connections para saber la fuente
        print("\n=== CONEXIONES ===")
        result = db.execute(text("""
            SELECT id, name, connection_type, host, database_name
            FROM connections
            ORDER BY id
        """))
        
        for row in result:
            print(f"  ID {row[0]}: {row[1]} ({row[2]}) - {row[3]}/{row[4]}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_origen_tabla_209()
