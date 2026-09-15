#!/usr/bin/env python3
"""Script para generar registros de staging para subcategoría 116."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

import importlib
import backend.app.api.endpoints.mapeo as mapeo_module
importlib.reload(mapeo_module)

from backend.app.core.database import get_dest_db
from backend.app.api.endpoints.mapeo import generate_to_cf_diariol

def generate_staging_116():
    db = next(get_dest_db())
    
    try:
        print("=== GENERANDO REGISTROS DE STAGING PARA SUBCATEGORÍA 116 ===")
        
        # Llamar a la función de generación
        result = generate_to_cf_diariol(
            body={
                "company_id": 7,
                "subcategoria_id": 116
            },
            db=db
        )
        print(f"Resultado: {result}")
        
        print("\nVerificando ccodcue en staging...")
        from sqlalchemy import text
        result = db.execute(text("""
            SELECT DISTINCT ccodcue, COUNT(*) as total
            FROM cf_diariol
            WHERE subcategoria_id = 116
            GROUP BY ccodcue
            ORDER BY ccodcue
        """))
        
        for row in result:
            print(f"   ccodcue: {row[0]} | Total: {row[1]}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    generate_staging_116()
