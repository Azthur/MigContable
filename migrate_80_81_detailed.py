#!/usr/bin/env python3
"""Script para migrar subcategorías 80 y 81 con detalle de errores."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

import importlib
import backend.app.api.endpoints.mapeo as mapeo_module
importlib.reload(mapeo_module)

from backend.app.core.database import get_dest_db
from backend.app.api.endpoints.mapeo import _migrate_to_final_internal

def migrate_80_81_detailed():
    db = next(get_dest_db())
    
    try:
        print("=== MIGRANDO SUBCATEGORÍAS 80 Y 81 CON DETALLE ===")
        
        subcats = [(80, 4), (81, 5)]
        
        for subcat_id, company_id in subcats:
            print(f"\n{'='*60}")
            print(f"Migrando subcategoría {subcat_id} (company_id={company_id})")
            print(f"{'='*60}")
            try:
                result = _migrate_to_final_internal(
                    company_id=company_id,
                    subcategoria_id=subcat_id,
                    allow_overwrite=True,
                    db=db
                )
                if isinstance(result, dict):
                    print(f"Mensaje: {result.get('message', 'Sin mensaje')}")
                    print(f"Líneas: {result.get('migrated_lineas', 0)}, Cabeceras: {result.get('migrated_cabeceras', 0)}")
                    if 'failed_rows' in result and result['failed_rows']:
                        print(f"Errores: {len(result['failed_rows'])}")
                        for error in result['failed_rows']:
                            print(f"  - {error}")
                else:
                    print(f"Resultado: {result}")
            except Exception as e:
                print(f"Error: {str(e)}")
                import traceback
                traceback.print_exc()
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_80_81_detailed()
