#!/usr/bin/env python3
"""Script para actualizar ccodcue en staging después de la generación."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def update_ccodcue_after_generation():
    db = next(get_dest_db())
    
    try:
        print("=== ACTUALIZANDO CCODCUE EN STAGING DESPUÉS DE GENERACIÓN ===")
        
        # Actualizar ccodcue con el valor por defecto 469901 (igual que subcategoría 81)
        result = db.execute(text("""
            UPDATE cf_diariol
            SET ccodcue = '469901'
            WHERE subcategoria_id = 116
            AND (ccodcue IS NULL OR ccodcue = '-' OR ccodcue = '')
        """))
        print(f"Registros actualizados: {result.rowcount}")
        
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
            print(f"  ccodcue: {row[0]} | Total: {row[1]}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_ccodcue_after_generation()
