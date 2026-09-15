#!/usr/bin/env python3
"""Script para actualizar cledmcper en staging para subcategoría 116."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def update_cledmcper_116():
    db = next(get_dest_db())
    
    try:
        print("=== ACTUALIZANDO CLEDMCPER EN STAGING PARA SUBCATEGORÍA 116 ===")
        
        # Actualizar cledmcper con el valor de cper
        result = db.execute(text("""
            UPDATE cf_diariol
            SET cledmcper = cper
            WHERE subcategoria_id = 116
            AND (cledmcper IS NULL OR cledmcper = '')
        """))
        print(f"Registros actualizados: {result.rowcount}")
        
        db.commit()
        
        print("\nVerificando cledmcper en staging...")
        result = db.execute(text("""
            SELECT DISTINCT cledmcper, COUNT(*) as total
            FROM cf_diariol
            WHERE subcategoria_id = 116
            GROUP BY cledmcper
            ORDER BY cledmcper
        """))
        
        for row in result:
            print(f"  cledmcper: {row[0]} | Total: {row[1]}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_cledmcper_116()
