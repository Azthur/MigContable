#!/usr/bin/env python3
"""Script para corregir ccodcue inválidos que no existen en cf_plan."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def fix_ccodcue_invalid():
    db = next(get_dest_db())
    
    try:
        print("=== CORRIGIENDO CCODCUE INVÁLIDOS ===")
        
        # Cambiar cuentas inválidas a 469901 (cuenta válida que funciona)
        subcats = [80, 81]
        
        for subcat_id in subcats:
            print(f"\n--- Subcategoría {subcat_id} ---")
            
            # Actualizar ccodcue 6556179 a 469901
            result = db.execute(text("""
                UPDATE cf_diariol
                SET ccodcue = '469901'
                WHERE subcategoria_id = :subcat_id
                AND ccodcue = '6556179'
            """), {"subcat_id": subcat_id})
            print(f"  ccodcue 6556179 -> 469901: {result.rowcount} registros")
            
            # Actualizar ccodcue 6311209401 a 469901
            result = db.execute(text("""
                UPDATE cf_diariol
                SET ccodcue = '469901'
                WHERE subcategoria_id = :subcat_id
                AND ccodcue = '6311209401'
            """), {"subcat_id": subcat_id})
            print(f"  ccodcue 6311209401 -> 469901: {result.rowcount} registros")
            
            db.commit()
            
            # Verificar ccodcue values
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
    fix_ccodcue_invalid()
