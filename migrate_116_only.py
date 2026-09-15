#!/usr/bin/env python3
"""Script para migrar solo subcategoría 116 a Contasis."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

import importlib
import backend.app.api.endpoints.mapeo as mapeo_module
importlib.reload(mapeo_module)

from backend.app.core.database import get_dest_db
from backend.app.api.endpoints.mapeo import _migrate_to_final_internal

def migrate_116_only():
    db = next(get_dest_db())
    
    try:
        print("=== MIGRANDO SUBCATEGORÍA 116 A CONTASIS ===")
        
        result = _migrate_to_final_internal(
            company_id=7,
            subcategoria_id=116,
            allow_overwrite=True,
            db=db
        )
        
        if isinstance(result, dict):
            print(f"Mensaje: {result.get('message', 'Sin mensaje')}")
            print(f"Líneas migradas: {result.get('migrated_lineas', 0)}")
            print(f"Cabeceras migradas: {result.get('migrated_cabeceras', 0)}")
        else:
            print(f"Resultado: {result}")
        
        print("\nVerificando estado final en staging...")
        from sqlalchemy import text
        result = db.execute(text("""
            SELECT subcategoria_id, estado, COUNT(*) as total
            FROM cf_diariol 
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
    finally:
        db.close()

if __name__ == "__main__":
    migrate_116_only()
