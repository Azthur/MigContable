#!/usr/bin/env python3
"""Script para revisar solo el esquema de computed_column_rules."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def check_computed_columns_schema_only():
    db = next(get_dest_db())
    
    try:
        print("=== ESQUEMA DE COMPUTED_COLUMN_RULES ===")
        result = db.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'computed_column_rules'
            ORDER BY ordinal_position
        """))
        
        columns = []
        for row in result:
            columns.append(row[0])
            print(f"  {row[0]}: {row[1]}")
            
        print(f"\nColumnas encontradas: {columns}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_computed_columns_schema_only()
