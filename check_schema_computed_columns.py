#!/usr/bin/env python3
"""Script para revisar el esquema de computed_column_rules."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def check_schema_computed_columns():
    db = next(get_dest_db())
    
    try:
        print("=== ESQUEMA DE COMPUTED_COLUMN_RULES ===")
        result = db.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'computed_column_rules'
            ORDER BY ordinal_position
        """))
        
        for row in result:
            print(f"  {row[0]}: {row[1]}")
        
        print("\n=== DATOS DE COMPUTED_COLUMN_RULES ===")
        result = db.execute(text("""
            SELECT * FROM computed_column_rules
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
    check_schema_computed_columns()
