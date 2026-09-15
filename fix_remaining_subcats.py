#!/usr/bin/env python3
"""Script para corregir ccodcue y otros campos en subcategorías restantes."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def fix_remaining_subcats():
    db = next(get_dest_db())
    
    try:
        print("=== CORRIGIENDO CAMPOS EN SUBCATEGORÍAS RESTANTES ===")
        
        subcats = [80, 81, 82]
        
        for subcat_id in subcats:
            print(f"\n--- Subcategoría {subcat_id} ---")
            
            # Actualizar ccodcue
            result = db.execute(text("""
                UPDATE cf_diariol
                SET ccodcue = '469901'
                WHERE subcategoria_id = :subcat_id
                AND (ccodcue IS NULL OR ccodcue = '-' OR ccodcue = '')
            """), {"subcat_id": subcat_id})
            print(f"  ccodcue actualizados: {result.rowcount}")
            
            # Actualizar clecvper
            result = db.execute(text("""
                UPDATE cf_diariol
                SET clecvper = cper
                WHERE subcategoria_id = :subcat_id
                AND (clecvper IS NULL OR clecvper = '')
            """), {"subcat_id": subcat_id})
            print(f"  clecvper actualizados: {result.rowcount}")
            
            # Actualizar cledmcper
            result = db.execute(text("""
                UPDATE cf_diariol
                SET cledmcper = cper
                WHERE subcategoria_id = :subcat_id
                AND (cledmcper IS NULL OR cledmcper = '')
            """), {"subcat_id": subcat_id})
            print(f"  cledmcper actualizados: {result.rowcount}")
            
            # Actualizar estado de cabeceras
            result = db.execute(text("""
                UPDATE cf_diario
                SET estado = '1'
                WHERE subcategoria_id = :subcat_id
                AND estado = '0'
            """), {"subcat_id": subcat_id})
            print(f"  cabeceras estado actualizados: {result.rowcount}")
            
            db.commit()
            
            # Verificar ccodcue
            result = db.execute(text("""
                SELECT DISTINCT ccodcue, COUNT(*) as total
                FROM cf_diariol
                WHERE subcategoria_id = :subcat_id
                GROUP BY ccodcue
                ORDER BY ccodcue
            """), {"subcat_id": subcat_id})
            
            print("  ccodcue values:")
            for row in result:
                print(f"    {row[0]}: {row[1]}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_remaining_subcats()
