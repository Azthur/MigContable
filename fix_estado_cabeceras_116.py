#!/usr/bin/env python3
"""Script para cambiar estado de cabeceras de '0' a '1' en subcategoría 116."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def fix_estado_cabeceras_116():
    db = next(get_dest_db())
    
    try:
        print("=== CAMBIANDO ESTADO DE CABECERAS DE SUBCATEGORÍA 116 ===")
        
        result = db.execute(text("""
            UPDATE cf_diario 
            SET estado = '1'
            WHERE subcategoria_id = 116
            AND estado = '0'
        """))
        
        print(f"Registros actualizados: {result.rowcount}")
        
        db.commit()
        
        print("\n=== VERIFICANDO RESULTADOS ===")
        result = db.execute(text("""
            SELECT subcategoria_id, estado, COUNT(*) as total
            FROM cf_diario 
            WHERE subcategoria_id = 116
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
    fix_estado_cabeceras_116()
