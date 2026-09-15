#!/usr/bin/env python3
"""Script para revisar el esquema de table_selections."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def check_schema_table_selections():
    db = next(get_dest_db())
    
    try:
        print("=== ESQUEMA DE TABLE_SELECTIONS ===")
        result = db.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'table_selections'
            ORDER BY ordinal_position
        """))
        
        for row in result:
            print(f"  {row[0]}: {row[1]}")
        
        print("\n=== DATOS DE TABLE_SELECTIONS ===")
        result = db.execute(text("""
            SELECT * FROM table_selections
            WHERE table_name ILIKE '%planilla%'
            ORDER BY company_id
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
    check_schema_table_selections()
