#!/usr/bin/env python3
"""Script para revisar los ETL pipelines del libro 209."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def check_etl_209():
    db = next(get_dest_db())
    
    try:
        print("=== ETL PIPELINES DEL LIBRO 209 ===")
        result = db.execute(text("""
            SELECT * FROM etl_pipeline_config
            WHERE description ILIKE '%209%'
            ORDER BY id
        """))
        
        for row in result:
            print(f"  ID {row[0]}: {row[3]}")
            print(f"    Activo: {row[4]} | Schedule: {row[5]} - {row[6]}")
            print(f"    Config: {row[10]}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_etl_209()
