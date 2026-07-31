#!/usr/bin/env python3
"""Script para encontrar table_selection_id para company_id 7."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def find_table_selection_company():
    db = next(get_dest_db())
    
    try:
        print("=== BUSCANDO TABLE_SELECTION_ID PARA COMPANY_ID 7 ===")
        
        result = db.execute(text("""
            SELECT ts.id, ts.table_name, ts.company_id
            FROM table_selections ts
            WHERE ts.company_id = 7
        """))
        
        for row in result:
            print(f"ID: {row[0]} | Tabla: {row[1]} | Company ID: {row[2]}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    find_table_selection_company()
