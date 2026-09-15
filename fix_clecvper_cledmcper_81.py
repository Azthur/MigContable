#!/usr/bin/env python3
"""Script para corregir clecvper y cledmcper en subcategoría 81."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def fix_clecvper_cledmcper_81():
    db = next(get_dest_db())
    
    try:
        print("=== CORRIGIENDO CLECVPER AND CLEDMPER EN SUBCATEGORÍA 81 ===")
        
        # Actualizar clecvper con el valor de cper
        result = db.execute(text("""
            UPDATE cf_diariol
            SET clecvper = cper
            WHERE subcategoria_id = 81
            AND (clecvper IS NULL OR clecvper = '')
        """))
        print(f"clecvper actualizados: {result.rowcount} registros")
        
        # Actualizar cledmcper con el valor de cper
        result = db.execute(text("""
            UPDATE cf_diariol
            SET cledmcper = cper
            WHERE subcategoria_id = 81
            AND (cledmcper IS NULL OR cledmcper = '')
        """))
        print(f"cledmcper actualizados: {result.rowcount} registros")
        
        # Actualizar estado de '0' a '1'
        result = db.execute(text("""
            UPDATE cf_diariol
            SET estado = '1'
            WHERE subcategoria_id = 81
            AND estado = '0'
        """))
        print(f"Estado actualizados: {result.rowcount} registros")
        
        db.commit()
        
        print("\n=== VERIFICANDO CORRECCIÓN ===")
        result = db.execute(text("""
            SELECT subcategoria_id, estado, COUNT(*) as total
            FROM cf_diariol 
            WHERE subcategoria_id = 81
            GROUP BY subcategoria_id, estado
            ORDER BY subcategoria_id, estado
        """))
        
        for row in result:
            print(f"  Subcategoría {row[0]} | Estado '{row[1]}': {row[2]} registros")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_clecvper_cledmcper_81()
