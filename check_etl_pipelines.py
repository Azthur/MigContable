#!/usr/bin/env python3
"""Script para revisar los ETL pipelines configurados."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def check_etl_pipelines():
    db = next(get_dest_db())
    
    try:
        print("=== ETL PIPELINES CONFIGURADOS ===")
        result = db.execute(text("""
            SELECT id, name, description, is_active, company_id
            FROM etl_pipeline_config
            ORDER BY company_id, name
        """))
        
        for row in result:
            print(f"  ID {row[0]}: {row[1]} (company_id: {row[4]})")
            print(f"    Descripción: {row[2]}")
            print(f"    Activo: {row[3]}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_etl_pipelines()
