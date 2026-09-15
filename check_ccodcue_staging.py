#!/usr/bin/env python3
"""Script para revisar valores de ccodcue en staging de subcategorías 81 y 116."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def check_ccodcue_staging():
    db = next(get_dest_db())
    
    try:
        print("=== VALORES DE CCODCUE EN STAGING ===")
        
        # Revisar ccodcue en subcategoría 81
        print("\nSubcategoría 81 (YLV Nature):")
        result = db.execute(text("""
            SELECT DISTINCT ccodcue, COUNT(*) as total
            FROM cf_diariol
            WHERE subcategoria_id = 81
            GROUP BY ccodcue
            ORDER BY ccodcue
        """))
        
        for row in result:
            print(f"  ccodcue: {row[0]} | Total: {row[1]}")
        
        # Revisar ccodcue en subcategoría 116
        print("\nSubcategoría 116 (YLV Grupo):")
        result = db.execute(text("""
            SELECT DISTINCT ccodcue, COUNT(*) as total
            FROM cf_diariol
            WHERE subcategoria_id = 116
            GROUP BY ccodcue
            ORDER BY ccodcue
        """))
        
        for row in result:
            print(f"  ccodcue: {row[0]} | Total: {row[1]}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_ccodcue_staging()
