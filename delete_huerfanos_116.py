#!/usr/bin/env python3
"""Script para eliminar registros huérfanos de staging para subcategoría 116."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def delete_huerfanos_116():
    db = next(get_dest_db())
    
    try:
        print("=== ELIMINANDO REGISTROS HUÉRFANOS DE SUBCATEGORÍA 116 ===")
        
        # Eliminar líneas del asiento huérfano
        result = db.execute(text("""
            DELETE FROM cf_diariol
            WHERE subcategoria_id = 116
            AND cper = '2026'
            AND cmes = '07'
            AND ccodori = '209'
            AND nasiento = 1
        """))
        print(f"Líneas eliminadas: {result.rowcount}")
        
        db.commit()
        
        print("\nVerificando registros restantes en staging...")
        result = db.execute(text("""
            SELECT cper, cmes, ccodori, nasiento, COUNT(*) as total
            FROM cf_diariol
            WHERE subcategoria_id = 116
            GROUP BY cper, cmes, ccodori, nasiento
            ORDER BY cper, cmes, nasiento
        """))
        
        for row in result:
            print(f"  cper: {row[0]} | cmes: {row[1]} | ccodori: {row[2]} | nasiento: {row[3]} | Total: {row[4]}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    delete_huerfanos_116()
