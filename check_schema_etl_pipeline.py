#!/usr/bin/env python3
"""Script para revisar el esquema de etl_pipeline_config."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def check_schema_etl_pipeline():
    db = next(get_dest_db())
    
    try:
        print("=== ESQUEMA DE ETL_PIPELINE_CONFIG ===")
        result = db.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'etl_pipeline_config'
            ORDER BY ordinal_position
        """))
        
        for row in result:
            print(f"  {row[0]}: {row[1]}")
        
        print("\n=== DATOS DE ETL_PIPELINE_CONFIG ===")
        result = db.execute(text("""
            SELECT * FROM etl_pipeline_config
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
    check_schema_etl_pipeline()
