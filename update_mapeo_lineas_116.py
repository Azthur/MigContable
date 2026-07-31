#!/usr/bin/env python3
"""Script para actualizar mapeo_lineas_asiento para subcategoría 116 con cuentas fijas."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def update_mapeo_lineas_116():
    db = next(get_dest_db())
    
    try:
        print("=== ACTUALIZANDO MAPEO_LINEAS_ASIENTO PARA SUBCATEGORÍA 116 ===")
        
        # Actualizar Orden 1 (Base Imponible - DEBE): ccodcue = '6556179'
        result = db.execute(text("""
            UPDATE mapeo_lineas_asiento
            SET mapeo_detalle = mapeo_detalle::jsonb || '{"ccodcue": "6556179"}'::jsonb
            WHERE subcategoria_id = 116 AND orden = 1
        """))
        print(f"Orden 1 actualizado: {result.rowcount} filas")
        
        # Actualizar Orden 4 (Total - HABER): ccodcue = '469901'
        result = db.execute(text("""
            UPDATE mapeo_lineas_asiento
            SET mapeo_detalle = mapeo_detalle::jsonb || '{"ccodcue": "469901"}'::jsonb
            WHERE subcategoria_id = 116 AND orden = 4
        """))
        print(f"Orden 4 actualizado: {result.rowcount} filas")
        
        db.commit()
        
        print("\n=== VERIFICANDO ACTUALIZACIÓN ===")
        result = db.execute(text("""
            SELECT id, subcategoria_id, orden, nombre_linea, 
                   mapeo_detalle->>'ccodcue' as ccodcue,
                   mapeo_detalle->>'ndebe' as ndebe,
                   mapeo_detalle->>'nhaber' as nhaber
            FROM mapeo_lineas_asiento
            WHERE subcategoria_id = 116
            ORDER BY orden
        """))
        
        for row in result:
            print(f"Orden {row[2]}: {row[3]}")
            print(f"  ccodcue: {row[4]} | ndebe: {row[5]} | nhaber: {row[6]}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_mapeo_lineas_116()
