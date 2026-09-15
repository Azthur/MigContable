#!/usr/bin/env python3
"""Script para actualizar ccodcue directamente en staging para subcategoría 116."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def update_ccodcue_116():
    db = next(get_dest_db())
    
    try:
        print("=== ACTUALIZANDO CCODCUE EN STAGING PARA SUBCATEGORÍA 116 ===")
        
        # Usar las mismas cuentas que la subcategoría 81
        # 469901 y 6556179
        print("\nActualizando ccodcue con valor por defecto 469901...")
        result = db.execute(text("""
            UPDATE cf_diariol
            SET ccodcue = '469901'
            WHERE subcategoria_id = 116
            AND ccodcue IS NULL
        """))
        print(f"   Registros actualizados: {result.rowcount}")
        
        db.commit()
        
        print("\nVerificando ccodcue en staging...")
        result = db.execute(text("""
            SELECT DISTINCT ccodcue, COUNT(*) as total
            FROM cf_diariol
            WHERE subcategoria_id = 116
            GROUP BY ccodcue
            ORDER BY ccodcue
        """))
        
        for row in result:
            print(f"   ccodcue: {row[0]} | Total: {row[1]}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_ccodcue_116()
