#!/usr/bin/env python3
"""Script para actualizar mapeo_lineas_asiento con cuenta válida en cf_plan."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text
import json

def update_mapeo_valid_account():
    db = next(get_dest_db())
    
    try:
        print("=== ACTUALIZANDO MAPEO_LINEAS_ASIENTO CON CUENTA VÁLIDA ===")
        
        # Actualizar la cuenta de débito de 6556179 a 6599004 (GASTOS DE MOVILIDAD DEL PERSONAL)
        # Usar Python para leer, modificar y actualizar el JSON
        result = db.execute(text("""
            SELECT id, mapeo_detalle
            FROM mapeo_lineas_asiento
            WHERE subcategoria_id IN (80, 81, 82, 83, 116)
            AND orden = 1
            AND mapeo_detalle->>'ccodcue' = '6556179'
        """))
        
        rows = result.fetchall()
        print(f"Registros encontrados: {len(rows)}")
        
        for row in rows:
            record_id = row[0]
            mapeo_detalle = row[1]
            
            # Modificar el JSON
            mapeo_detalle['ccodcue'] = '6599004'
            
            # Actualizar
            db.execute(text("""
                UPDATE mapeo_lineas_asiento
                SET mapeo_detalle = :mapeo_detalle
                WHERE id = :id
            """), {"mapeo_detalle": json.dumps(mapeo_detalle), "id": record_id})
        
        print(f"Registros actualizados: {len(rows)}")
        
        # Verificar la actualización
        result = db.execute(text("""
            SELECT subcategoria_id, orden, mapeo_detalle->>'ccodcue' as ccodcue
            FROM mapeo_lineas_asiento
            WHERE subcategoria_id IN (80, 81, 82, 83, 116)
            AND orden IN (1, 4)
            ORDER BY subcategoria_id, orden
        """))
        
        print("\nMapeo actualizado:")
        for row in result:
            print(f"  Subcategoría {row[0]} | Orden {row[1]} | ccodcue: {row[2]}")
        
        db.commit()
        print("\nActualización completada exitosamente")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_mapeo_valid_account()
