#!/usr/bin/env python3
"""Script para revisar el schema de mapeo_subcategorias."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def check_schema():
    db = next(get_dest_db())
    
    try:
        print("=== SCHEMA DE MAPEO_SUBCATEGORIAS ===")
        
        result = db.execute(text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'mapeo_subcategorias'
            ORDER BY ordinal_position
        """))
        
        for row in result:
            print(f"  {row[0]}: {row[1]}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_schema()
