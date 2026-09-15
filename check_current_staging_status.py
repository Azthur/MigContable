#!/usr/bin/env python3
"""Script para revisar el estado actual de staging después de ejecutar ETL."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def check_current_staging_status():
    db = next(get_dest_db())
    
    try:
        print("=== ESTADO ACTUAL DE STAGING DESPUÉS DE ETL ===")
        
        # Líneas de detalle
        result = db.execute(text("""
            SELECT subcategoria_id, estado, COUNT(*) as total
            FROM cf_diariol 
            WHERE subcategoria_id IN (80, 81, 82, 83, 116)
            GROUP BY subcategoria_id, estado
            ORDER BY subcategoria_id, estado
        """))
        
        print("Líneas de detalle (cf_diariol):")
        for row in result:
            print(f"  Subcategoría {row[0]} | Estado '{row[1]}': {row[2]} registros")
        
        # Cabeceras
        result = db.execute(text("""
            SELECT subcategoria_id, estado, COUNT(*) as total
            FROM cf_diario 
            WHERE subcategoria_id IN (80, 81, 82, 83, 116)
            GROUP BY subcategoria_id, estado
            ORDER BY subcategoria_id, estado
        """))
        
        print("\nCabeceras (cf_diario):")
        for row in result:
            print(f"  Subcategoría {row[0]} | Estado '{row[1]}': {row[2]} registros")
        
        # Verificar campos problemáticos
        print("\n=== VERIFICANDO CAMPOS PROBLEMÁTICOS ===")
        
        # Verificar clecvper NULL
        result = db.execute(text("""
            SELECT subcategoria_id, COUNT(*) as total
            FROM cf_diariol 
            WHERE subcategoria_id IN (80, 81, 82, 83, 116)
            AND (clecvper IS NULL OR clecvper = '')
            GROUP BY subcategoria_id
            ORDER BY subcategoria_id
        """))
        
        print("clecvper NULL:")
        for row in result:
            print(f"  Subcategoría {row[0]}: {row[1]} registros")
        
        # Verificar cledmcper NULL
        result = db.execute(text("""
            SELECT subcategoria_id, COUNT(*) as total
            FROM cf_diariol 
            WHERE subcategoria_id IN (80, 81, 82, 83, 116)
            AND (cledmcper IS NULL OR cledmcper = '')
            GROUP BY subcategoria_id
            ORDER BY subcategoria_id
        """))
        
        print("cledmcper NULL:")
        for row in result:
            print(f"  Subcategoría {row[0]}: {row[1]} registros")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_current_staging_status()
