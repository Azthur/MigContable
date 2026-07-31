#!/usr/bin/env python3
"""Script para revisar config_account_mapping."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def check_config_account_mapping():
    db = next(get_dest_db())
    
    try:
        print("=== ESTRUCTURA DE CONFIG_ACCOUNT_MAPPING ===")
        result = db.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'config_account_mapping'
            ORDER BY ordinal_position
        """))
        
        for row in result:
            print(f"  {row[0]}: {row[1]}")
        
        print("\n=== DATOS DE CONFIG_ACCOUNT_MAPPING ===")
        result = db.execute(text("""
            SELECT * FROM config_account_mapping
            LIMIT 10
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
    check_config_account_mapping()
