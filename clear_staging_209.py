#!/usr/bin/env python3
"""Script para limpiar registros de staging del libro 209 para regeneración desde ETL."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def clear_staging_209():
    db = next(get_dest_db())
    
    try:
        print("=== LIMPIANDO STAGING DEL LIBRO 209 ===")
        
        subcats = [80, 81, 82, 83, 116]
        
        for subcat_id in subcats:
            print(f"\n--- Subcategoría {subcat_id} ---")
            
            # Eliminar líneas de detalle
            result = db.execute(text("""
                DELETE FROM cf_diariol
                WHERE subcategoria_id = :subcat_id
            """), {"subcat_id": subcat_id})
            print(f"  Líneas eliminadas: {result.rowcount}")
            
            # Eliminar cabeceras
            result = db.execute(text("""
                DELETE FROM cf_diario
                WHERE subcategoria_id = :subcat_id
            """), {"subcat_id": subcat_id})
            print(f"  Cabeceras eliminadas: {result.rowcount}")
        
        db.commit()
        
        print("\n=== VERIFICANDO LIMPIEZA ===")
        result = db.execute(text("""
            SELECT subcategoria_id, COUNT(*) as total
            FROM cf_diariol 
            WHERE subcategoria_id IN (80, 81, 82, 83, 116)
            GROUP BY subcategoria_id
            ORDER BY subcategoria_id
        """))
        
        for row in result:
            print(f"  Subcategoría {row[0]}: {row[1]} registros")
        
        print("\nStaging limpio. Ahora puedes usar el ETL para regenerar y migrar los datos.")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    clear_staging_209()
