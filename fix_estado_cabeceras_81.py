#!/usr/bin/env python3
"""Script para corregir estado de cabeceras en subcategoría 81."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def fix_estado_cabeceras_81():
    db = next(get_dest_db())
    
    try:
        print("=== CORRIGIENDO ESTADO DE CABECERAS EN SUBCATEGORÍA 81 ===")
        
        # Actualizar estado de cabeceras de '0' a '1'
        result = db.execute(text("""
            UPDATE cf_diario
            SET estado = '1'
            WHERE subcategoria_id = 81
            AND estado = '0'
        """))
        print(f"Estado de cabeceras actualizados: {result.rowcount} registros")
        
        db.commit()
        
        print("\n=== VERIFICANDO CORRECCIÓN ===")
        result = db.execute(text("""
            SELECT subcategoria_id, estado, COUNT(*) as total
            FROM cf_diario 
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
    fix_estado_cabeceras_81()
