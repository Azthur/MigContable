#!/usr/bin/env python3
"""Script minimal para migrar registros del libro 209 a Contasis."""
import sys
sys.path.insert(0, '/app')

# Desactivar logging
import logging
logging.disable(logging.CRITICAL)

import importlib
import backend.app.api.endpoints.mapeo as mapeo_module
importlib.reload(mapeo_module)

from backend.app.core.database import get_dest_db
from backend.app.api.endpoints.mapeo import _migrate_to_final_internal

def migrate_book_209():
    db = next(get_dest_db())
    
    try:
        print("=== MIGRANDO REGISTROS DEL LIBRO 209 A CONTASIS ===")
        
        subcats = [(80, 4), (81, 5), (82, 6), (83, 1), (116, 7)]
        
        for subcat_id, company_id in subcats:
            print(f"\nSubcategoría {subcat_id} (company_id={company_id}):")
            try:
                result = _migrate_to_final_internal(
                    company_id=company_id,
                    subcategoria_id=subcat_id,
                    allow_overwrite=True,
                    db=db
                )
                if isinstance(result, dict):
                    print(f"  {result.get('message', 'Sin mensaje')}")
                    print(f"  Líneas: {result.get('migrated_lineas', 0)}, Cabeceras: {result.get('migrated_cabeceras', 0)}")
                else:
                    print(f"  {result}")
            except Exception as e:
                print(f"  Error: {str(e)}")
            
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    migrate_book_209()
