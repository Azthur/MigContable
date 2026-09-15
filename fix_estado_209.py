#!/usr/bin/env python3
"""Script para cambiar estado de '0' a '1' en registros del libro 209."""
import sys
sys.path.insert(0, '/app')

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def fix_estado_209():
    db = next(get_dest_db())
    
    try:
        print("=== CAMBIANDO ESTADO DE '0' A '1' ===")
        
        result = db.execute(text("""
            UPDATE cf_diariol 
            SET estado = '1'
            WHERE subcategoria_id IN (80,81,82,83,116)
            AND estado = '0'
        """))
        
        print(f"Registros actualizados: {result.rowcount}")
        
        # También actualizar cabeceras
        result = db.execute(text("""
            UPDATE cf_diario 
            SET estado = '1'
            WHERE subcategoria_id IN (80,81,82,83,116)
            AND estado = '0'
        """))
        
        print(f"Cabeceras actualizadas: {result.rowcount}")
        
        db.commit()
        
        print("\n=== VERIFICANDO RESULTADOS ===")
        result = db.execute(text("""
            SELECT subcategoria_id, estado, COUNT(*) as total
            FROM cf_diariol 
            WHERE subcategoria_id IN (80,81,82,83,116)
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
    fix_estado_209()
