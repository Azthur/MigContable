#!/usr/bin/env python3
"""Script para revisar el mapeo de ccodcue en subcategorías 81 y 116."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def check_mapeo_ccodcue():
    db = next(get_dest_db())
    
    try:
        print("=== REVISANDO MAPEO DE CCODCUE ===")
        
        # Obtener mapeo de subcategorías 81 y 116
        result = db.execute(text("""
            SELECT id, nombre, mapeo_cabecera
            FROM mapeo_subcategorias
            WHERE id IN (81, 116)
            ORDER BY id
        """))
        
        for row in result:
            print(f"\nSubcategoría {row[0]}: {row[1]}")
            print(f"Mapeo cabecera: {row[2]}")
            
            # Parsear el JSON para buscar ccodcue
            import json
            if row[2]:
                try:
                    mapeo = json.loads(row[2])
                    for key, value in mapeo.items():
                        if 'ccodcue' in key.lower() or 'cuenta' in key.lower():
                            print(f"  {key}: {value}")
                except:
                    print(f"  Error al parsear JSON")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_mapeo_ccodcue()
