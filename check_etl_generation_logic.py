#!/usr/bin/env python3
"""Script para revisar cómo el ETL genera los datos."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def check_etl_generation_logic():
    db = next(get_dest_db())
    
    try:
        print("=== REVISANDO MUESTRA DE DATOS GENERADOS ===")
        
        # Verificar una muestra de datos generados
        result = db.execute(text("""
            SELECT cper, clecvper, cledmcper, ccodcue, estado
            FROM cf_diariol 
            WHERE subcategoria_id = 81
            LIMIT 5
        """))
        
        print("Muestra de datos generados:")
        for row in result:
            print(f"  cper: {row[0]} | clecvper: {row[1]} | cledmcper: {row[2]} | ccodcue: {row[3]} | estado: {row[4]}")
        
        # Verificar si cper tiene valor
        result = db.execute(text("""
            SELECT DISTINCT cper, COUNT(*) as total
            FROM cf_diariol 
            WHERE subcategoria_id = 81
            GROUP BY cper
        """))
        
        print("\nValores de cper:")
        for row in result:
            print(f"  cper: {row[0]} | Total: {row[1]}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_etl_generation_logic()
