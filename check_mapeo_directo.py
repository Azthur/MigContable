#!/usr/bin/env python3
"""Script para revisar el mapeo directo de subcategorías 81 y 116."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def check_mapeo_directo():
    db = next(get_dest_db())
    
    try:
        print("=== MAPEO DIRECTO DE SUBCATEGORÍAS 81 Y 116 ===")
        
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
            
            print(f"\nMapeo cabecera (tipo: {type(row[2])}):")
            if row[2]:
                if isinstance(row[2], dict):
                    for key, value in row[2].items():
                        print(f"  {key}: {value}")
                else:
                    print(f"  {row[2]}")
            
            print(f"\nPares redondeo (tipo: {type(row[3])}):")
            if row[3]:
                if isinstance(row[3], list):
                    for item in row[3]:
                        print(f"  {item}")
                elif isinstance(row[3], dict):
                    for key, value in row[3].items():
                        print(f"  {key}: {value}")
                else:
                    print(f"  {row[3]}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_mapeo_directo()
