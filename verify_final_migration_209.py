#!/usr/bin/env python3
"""Script para verificar el estado final de la migración del libro 209."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def verify_final_migration_209():
    db = next(get_dest_db())
    
    try:
        print("=== ESTADO FINAL DE MIGRACIÓN DEL LIBRO 209 ===")
        
        # Verificar estado en staging por subcategoría
        result = db.execute(text("""
            SELECT subcategoria_id, estado, COUNT(*) as total
            FROM cf_diariol 
            WHERE subcategoria_id IN (80,81,82,83,116)
            GROUP BY subcategoria_id, estado
            ORDER BY subcategoria_id, estado
        """))
        
        print("\nEstado en staging (cf_diariol):")
        for row in result:
            print(f"  Subcategoría {row[0]} | Estado '{row[1]}': {row[2]} registros")
        
        # Verificar cabeceras en staging
        result = db.execute(text("""
            SELECT subcategoria_id, estado, COUNT(*) as total
            FROM cf_diario 
            WHERE subcategoria_id IN (80,81,82,83,116)
            GROUP BY subcategoria_id, estado
            ORDER BY subcategoria_id, estado
        """))
        
        print("\nEstado en staging (cf_diario):")
        for row in result:
            print(f"  Subcategoría {row[0]} | Estado '{row[1]}': {row[2]} cabeceras")
        
        # Verificar cper values
        result = db.execute(text("""
            SELECT subcategoria_id, cper, COUNT(*) as total
            FROM cf_diariol 
            WHERE subcategoria_id IN (80,81,82,83,116)
            GROUP BY subcategoria_id, cper
            ORDER BY subcategoria_id, cper
        """))
        
        print("\nValores de cper por subcategoría:")
        for row in result:
            print(f"  Subcategoría {row[0]} | cper: {row[1]} | Total: {row[2]}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verify_final_migration_209()
