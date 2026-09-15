#!/usr/bin/env python3
"""Script para revisar las conexiones de origen."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def check_source_connections():
    db = next(get_dest_db())
    
    try:
        print("=== TABLAS DE CONEXIONES ===")
        result = db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            AND (table_name ILIKE '%connection%' OR table_name ILIKE '%source%')
            ORDER BY table_name
        """))
        
        for row in result:
            print(f"  {row[0]}")
        
        # Revisar la tabla source_connections
        print("\n=== DATOS DE SOURCE_CONNECTIONS ===")
        result = db.execute(text("""
            SELECT * FROM source_connections
            ORDER BY id
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
    check_source_connections()
