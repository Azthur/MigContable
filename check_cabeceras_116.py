#!/usr/bin/env python3
"""Script para verificar si hay cabeceras en staging para subcategoría 116."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def check_cabeceras_116():
    db = next(get_dest_db())
    
    try:
        print("=== VERIFICANDO CABECERAS EN STAGING PARA SUBCATEGORÍA 116 ===")
        
        result = db.execute(text("""
            SELECT COUNT(*) as total
            FROM cf_diario
            WHERE subcategoria_id = 116
        """))
        
        total = result.scalar()
        print(f"Total de cabeceras: {total}")
        
        if total > 0:
            print("\nMuestra de cabeceras:")
            result = db.execute(text("""
                SELECT cper, cmes, ccodori, nasiento, estado
                FROM cf_diario
                WHERE subcategoria_id = 116
                LIMIT 5
            """))
            
            for row in result:
                print(f"  cper: {row[0]} | cmes: {row[1]} | ccodori: {row[2]} | nasiento: {row[3]} | estado: {row[4]}")
        else:
            print("No hay cabeceras en staging.")
            
        # Verificar configuración de la subcategoría
        print("\n=== CONFIGURACIÓN DE SUBCATEGORÍA 116 ===")
        result = db.execute(text("""
            SELECT generate_headers, generate_details
            FROM mapeo_subcategorias
            WHERE id = 116
        """))
        
        for row in result:
            print(f"  generate_headers: {row[0]}")
            print(f"  generate_details: {row[1]}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_cabeceras_116()
