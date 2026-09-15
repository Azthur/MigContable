#!/usr/bin/env python3
"""Script para verificar si hay registros en staging para subcategoría 116."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def check_staging_116():
    db = next(get_dest_db())
    
    try:
        print("=== VERIFICANDO REGISTROS EN STAGING PARA SUBCATEGORÍA 116 ===")
        
        result = db.execute(text("""
            SELECT COUNT(*) as total
            FROM cf_diariol
            WHERE subcategoria_id = 116
        """))
        
        total = result.scalar()
        print(f"Total de registros: {total}")
        
        if total > 0:
            print("\nMuestra de registros:")
            result = db.execute(text("""
                SELECT ccodcue, cper, cmes, nasiento, estado
                FROM cf_diariol
                WHERE subcategoria_id = 116
                LIMIT 5
            """))
            
            for row in result:
                print(f"  ccodcue: {row[0]} | cper: {row[1]} | cmes: {row[2]} | nasiento: {row[3]} | estado: {row[4]}")
        else:
            print("No hay registros en staging. Necesito generarlos primero.")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_staging_116()
