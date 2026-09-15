#!/usr/bin/env python3
"""Script para verificar estado de subcategorías del libro 209."""
import sys
sys.path.insert(0, '/app')

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def check_subcategorias_209():
    db = next(get_dest_db())
    
    try:
        print("=== VERIFICANDO SUBCATEGORÍAS DEL LIBRO 209 ===")
        
        result = db.execute(text("""
            SELECT s.id, s.nombre, s.is_active, c.company_id
            FROM mapeo_subcategorias s
            JOIN mapeo_categorias c ON s.categoria_id = c.id
            WHERE s.id IN (80,81,82,83,116)
            ORDER BY s.id
        """))
        
        for row in result:
            print(f"  ID: {row[0]} | Nombre: {row[1]} | Activa: {row[2]} | Company ID: {row[3]}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_subcategorias_209()
