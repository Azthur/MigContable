#!/usr/bin/env python3
"""Script para revisar el mapeo completo de subcategorías 81 y 116."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def check_mapeo_completo():
    db = next(get_dest_db())
    
    try:
        print("=== MAPEO COMPLETO DE SUBCATEGORÍAS 81 Y 116 ===")
        
        result = db.execute(text("""
            SELECT id, nombre, mapeo_cabecera, pares_redondeo
            FROM mapeo_subcategorias
            WHERE id IN (81, 116)
            ORDER BY id
        """))
        
        for row in result:
            print(f"\n{'='*60}")
            print(f"Subcategoría {row[0]}: {row[1]}")
            print(f"{'='*60}")
            
            import json
            if row[2]:
                try:
                    mapeo = json.loads(row[2])
                    print("\nMapeo cabecera:")
                    for key, value in mapeo.items():
                        print(f"  {key}: {value}")
                except Exception as e:
                    print(f"Error al parsear mapeo_cabecera: {e}")
            
            if row[3]:
                try:
                    pares = json.loads(row[3])
                    print("\nPares redondeo:")
                    for key, value in pares.items():
                        print(f"  {key}: {value}")
                except Exception as e:
                    print(f"Error al parsear pares_redondeo: {e}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_mapeo_completo()
