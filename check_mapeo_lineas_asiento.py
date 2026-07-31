#!/usr/bin/env python3
"""Script para revisar mapeo_lineas_asiento."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def check_mapeo_lineas_asiento():
    db = next(get_dest_db())
    
    try:
        print("=== ESTRUCTURA DE MAPEO_LINEAS_ASIENTO ===")
        result = db.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'mapeo_lineas_asiento'
            ORDER BY ordinal_position
        """))
        
        for row in result:
            print(f"  {row[0]}: {row[1]}")
        
        print("\n=== DATOS DE MAPEO_LINEAS_ASIENTO ===")
        result = db.execute(text("""
            SELECT * FROM mapeo_lineas_asiento
            WHERE subcategoria_id IN (80, 81, 82, 83, 116)
            ORDER BY subcategoria_id, orden
        """))
        
        for row in result:
            print(f"  {row}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_mapeo_lineas_asiento()
