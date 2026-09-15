#!/usr/bin/env python3
"""Script para revisar datos de origen de subcategorías 81 y 116."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def check_data_origen():
    db = next(get_dest_db())
    
    try:
        print("=== DATOS DE ORIGEN DE SUBCATEGORÍAS 81 Y 116 ===")
        
        # Revisar datos de origen para subcategoría 81
        print("\nSubcategoría 81 (YLV Nature) - Datos de origen:")
        result = db.execute(text("""
            SELECT "C_CodAux", "C_ctabaseF", "C_ctatotalF", idcontrol
            FROM finplanillamovilidaddet
            WHERE company_id = 5
            LIMIT 5
        """))
        
        for row in result:
            print(f"  C_CodAux: {row[0]} | C_ctabaseF: {row[1]} | C_ctatotalF: {row[2]} | idcontrol: {row[3]}")
        
        # Revisar datos de origen para subcategoría 116
        print("\nSubcategoría 116 (YLV Grupo) - Datos de origen:")
        result = db.execute(text("""
            SELECT "C_CodAux", "C_ctabaseF", "C_ctatotalF", idcontrol
            FROM finplanillamovilidaddet
            WHERE company_id = 7
            LIMIT 5
        """))
        
        for row in result:
            print(f"  C_CodAux: {row[0]} | C_ctabaseF: {row[1]} | C_ctatotalF: {row[2]} | idcontrol: {row[3]}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_data_origen()
