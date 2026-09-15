#!/usr/bin/env python3
"""Script para debug de errores de validación en registros del libro 209."""
import sys
sys.path.insert(0, '/app')

import importlib
import backend.app.api.endpoints.mapeo as mapeo_module
importlib.reload(mapeo_module)

from backend.app.core.database import get_dest_db
from backend.app.api.endpoints.mapeo import validate_staging_data
from sqlalchemy import text

def debug_validation_errors():
    db = next(get_dest_db())
    
    try:
        print("=== DEBUG DE ERRORES DE VALIDACIÓN ===")
        
        # Obtener subcategorías del libro 209
        subcat_ids = [80, 81, 82, 83, 116]
        
        for subcat_id in subcat_ids:
            print(f"\n--- Subcategoría {subcat_id} ---")
            try:
                result = validate_staging_data({
                    "company_id": 5,
                    "subcategoria_id": subcat_id
                }, db)
                print(f"  Resultado: {result}")
            except Exception as e:
                print(f"  Error: {e}")
                import traceback
                traceback.print_exc()
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_validation_errors()
