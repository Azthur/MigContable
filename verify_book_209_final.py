#!/usr/bin/env python3
"""Script para verificar el estado final del libro 209."""
import sys
sys.path.insert(0, '/app')

import importlib
import backend.app.api.endpoints.mapeo as mapeo_module
importlib.reload(mapeo_module)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def verify_book_209_final():
    db = next(get_dest_db())
    
    try:
        print("=== ESTADO FINAL DEL LIBRO 209 ===")
        
        result = db.execute(text("""
            SELECT subcategoria_id, estado, COUNT(*) as total
            FROM cf_diariol 
            WHERE subcategoria_id IN (80,81,82,83,116)
            GROUP BY subcategoria_id, estado
            ORDER BY subcategoria_id, estado
        """))
        
        for row in result:
            print(f"  Subcategoría {row[0]} | Estado '{row[1]}': {row[2]} registros")
        
        print("\n=== VALORES cper ===")
        result = db.execute(text("""
            SELECT cper, COUNT(*) as total
            FROM cf_diariol 
            WHERE subcategoria_id IN (80,81,82,83,116)
            GROUP BY cper
            ORDER BY total DESC
        """))
        
        for row in result:
            print(f"  cper='{row[0]}': {row[1]} registros")
        
        print("\n=== VALORES cmes ===")
        result = db.execute(text("""
            SELECT cmes, COUNT(*) as total
            FROM cf_diariol 
            WHERE subcategoria_id IN (80,81,82,83,116)
            GROUP BY cmes
            ORDER BY total DESC
        """))
        
        for row in result:
            print(f"  cmes='{row[0]}': {row[1]} registros")
            
        print("\n=== REGISTROS CON ESTADO '0' (ERROR) ===")
        result = db.execute(text("""
            SELECT subcategoria_id, idcontrol, cper, cmes, estado
            FROM cf_diariol 
            WHERE subcategoria_id IN (80,81,82,83,116)
            AND estado = '0'
            LIMIT 10
        """))
        
        error_count = 0
        for row in result:
            error_count += 1
            print(f"  Subcategoría {row[0]} | idcontrol={row[1]} | cper='{row[2]}' | cmes='{row[3]}' | estado='{row[4]}'")
        
        if error_count == 0:
            print("  ✓ No hay registros con estado '0'")
        else:
            print(f"  ⚠️ {error_count} registros con estado '0'")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verify_book_209_final()
