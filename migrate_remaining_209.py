#!/usr/bin/env python3
"""Script para migrar las subcategorías restantes del libro 209."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

import importlib
import backend.app.api.endpoints.mapeo as mapeo_module
importlib.reload(mapeo_module)

from backend.app.core.database import get_dest_db
from backend.app.api.endpoints.mapeo import _migrate_to_final_internal

def migrate_remaining_209():
    db = next(get_dest_db())
    
    try:
        print("=== MIGRANDO SUBCATEGORÍAS RESTANTES DEL LIBRO 209 ===")
        
        # Subcategorías pendientes con sus company_id correctos
        subcats = [
            (80, 4),  # YLV Industrias
            (81, 5),  # YLV Nature
            (82, 6),  # YLV Corpo
        ]
        
        for subcat_id, company_id in subcats:
            print(f"\nMigrando subcategoría {subcat_id} (company_id={company_id})...")
            try:
                result = _migrate_to_final_internal(
                    company_id=company_id,
                    subcategoria_id=subcat_id,
                    allow_overwrite=True,
                    db=db
                )
                if isinstance(result, dict):
                    print(f"  ✓ {result.get('message', 'Sin mensaje')}")
                    print(f"    Líneas: {result.get('migrated_lineas', 0)}, Cabeceras: {result.get('migrated_cabeceras', 0)}")
                else:
                    print(f"  {result}")
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
        
        print("\n=== ESTADO FINAL ===")
        from sqlalchemy import text
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
    finally:
        db.close()

if __name__ == "__main__":
    migrate_remaining_209()
