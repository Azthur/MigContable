#!/usr/bin/env python3
"""Script para revisar las conexiones."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def check_connections():
    db = next(get_dest_db())
    
    try:
        print("=== CONEXIONES CONFIGURADAS ===")
        result = db.execute(text("""
            SELECT id, name, connection_type, host, database_name, port
            FROM connections
            ORDER BY id
        """))
        
        for row in result:
            print(f"  ID {row[0]}: {row[1]} ({row[2]})")
            print(f"    Host: {row[3]}, DB: {row[4]}, Port: {row[5]}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_connections()
