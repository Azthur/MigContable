#!/usr/bin/env python3
"""Script para actualizar clecvper en staging para subcategoría 116."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def update_clecvper_116():
    db = next(get_dest_db())
    
    try:
        print("=== ACTUALIZANDO CLECVPER EN STAGING PARA SUBCATEGORÍA 116 ===")
        
        # Actualizar clecvper con el valor de cper
        result = db.execute(text("""
            UPDATE cf_diariol
            SET clecvper = cper
            WHERE subcategoria_id = 116
            AND (clecvper IS NULL OR clecvper = '')
        """))
        print(f"Registros actualizados: {result.rowcount}")
        
        db.commit()
        
        print("\nVerificando clecvper en staging...")
        result = db.execute(text("""
            SELECT DISTINCT clecvper, COUNT(*) as total
            FROM cf_diariol
            WHERE subcategoria_id = 116
            GROUP BY clecvper
            ORDER BY clecvper
        """))
        
        for row in result:
            print(f"  clecvper: {row[0]} | Total: {row[1]}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_clecvper_116()
