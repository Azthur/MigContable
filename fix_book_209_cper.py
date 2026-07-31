#!/usr/bin/env python3
"""Script para borrar registros con cper='nan ' y regenerar asientos del libro 209."""
import sys
sys.path.insert(0, '/app')

import importlib
import backend.app.api.endpoints.mapeo as mapeo_module
importlib.reload(mapeo_module)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def fix_book_209_cper():
    db = next(get_dest_db())
    
    try:
        print("=== BORRANDO REGISTROS CON cper='nan ' ===")
        result = db.execute(text("""
            DELETE FROM cf_diariol 
            WHERE subcategoria_id IN (80,81,82,83,116)
            AND estado = '0'
        """))
        print(f"Registros borrados: {result.rowcount}")
        
        # También borrar cabeceras huérfanas
        result = db.execute(text("""
            DELETE FROM cf_diario 
            WHERE subcategoria_id IN (80,81,82,83,116)
            AND estado = '0'
        """))
        print(f"Cabeceras borradas: {result.rowcount}")
        
        db.commit()
        
        print("\n=== REGENERANDO ASIENTOS DEL LIBRO 209 ===")
        from backend.app.api.endpoints.mapeo import generate_to_cf_diariol
        
        subcat_ids = [80, 81, 82, 83, 116]
        
        for subcat_id in subcat_ids:
            print(f"\nRegenerando para subcategoría {subcat_id}...")
            try:
                result = generate_to_cf_diariol(
                    {
                        "subcategoria_id": subcat_id,
                        "clear_previous": False,
                        "is_realtime": False
                    },
                    db
                )
                print(f"  Resultado: {result}")
            except Exception as e:
                print(f"  Error: {e}")
                import traceback
                traceback.print_exc()
        
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
        
        print("\n=== VERIFICANDO VALORES cper ===")
        result = db.execute(text("""
            SELECT cper, COUNT(*) as total
            FROM cf_diariol 
            WHERE subcategoria_id IN (80,81,82,83,116)
            GROUP BY cper
            ORDER BY total DESC
        """))
        
        for row in result:
            print(f"  cper='{row[0]}': {row[1]} registros")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_book_209_cper()
