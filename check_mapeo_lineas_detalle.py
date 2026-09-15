#!/usr/bin/env python3
"""Script para revisar el detalle de mapeo_lineas_asiento."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def check_mapeo_lineas_detalle():
    db = next(get_dest_db())
    
    try:
        print("=== DETALLE DE MAPEO_LINEAS_ASIENTO PARA SUBCATEGORÍA 116 ===")
        result = db.execute(text("""
            SELECT id, subcategoria_id, orden, nombre_linea, 
                   mapeo_detalle->>'ccodcue' as ccodcue,
                   mapeo_detalle->>'ndebe' as ndebe,
                   mapeo_detalle->>'nhaber' as nhaber,
                   condicion_aplicacion,
                   nivel,
                   is_active
            FROM mapeo_lineas_asiento
            WHERE subcategoria_id = 116
            ORDER BY orden
        """))
        
        for row in result:
            print(f"\nOrden {row[2]}: {row[3]}")
            print(f"  ccodcue: {row[4]}")
            print(f"  ndebe: {row[5]}")
            print(f"  nhaber: {row[6]}")
            print(f"  Condición: {row[7]}")
            print(f"  Nivel: {row[8]}")
            print(f"  Activo: {row[9]}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_mapeo_lineas_detalle()
