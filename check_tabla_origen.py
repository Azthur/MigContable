#!/usr/bin/env python3
"""Script para revisar tabla origen de subcategorías 81 y 116."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def check_tabla_origen():
    db = next(get_dest_db())
    
    try:
        print("=== TABLA ORIGEN DE SUBCATEGORÍAS 81 Y 116 ===")
        
        result = db.execute(text("""
            SELECT id, nombre, tabla_origen, schema_destino
            FROM mapeo_subcategorias
            WHERE id IN (81, 116)
            ORDER BY id
        """))
        
        for row in result:
            print(f"\nSubcategoría {row[0]}: {row[1]}")
            print(f"  Tabla origen: {row[2]}")
            print(f"  Schema destino: {row[3]}")
            
            # Revisar columnas de la tabla origen
            try:
                col_result = db.execute(text(f"""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = '{row[2]}'
                    ORDER BY ordinal_position
                """))
                
                print(f"  Columnas de {row[2]}:")
                cols = []
                for col_row in col_result:
                    cols.append(col_row[0])
                    if col_row[0] in ['ccodcue', 'cuenta', 'codcue', 'cuenta_contable']:
                        print(f"    *** {col_row[0]} ***")
                    else:
                        print(f"    {col_row[0]}")
            except Exception as e:
                print(f"  Error al obtener columnas: {e}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_tabla_origen()
