#!/usr/bin/env python3
"""Script simplificado para migrar registros del libro 209 a Contasis."""
import sys
sys.path.insert(0, '/app')

import importlib
import backend.app.api.endpoints.mapeo as mapeo_module
importlib.reload(mapeo_module)

from backend.app.core.database import get_dest_db
from backend.app.api.endpoints.mapeo import _migrate_to_final_internal

def migrate_book_209():
    db = next(get_dest_db())
    
    try:
        print("=== MIGRANDO REGISTROS DEL LIBRO 209 A CONTASIS ===")
        
        # Subcategorías con sus company_id correctos
        subcats = [
            (80, 4),  # YLV Industrias
            (81, 5),  # YLV Nature
            (82, 6),  # YLV Corpo
            (83, 1),  # YLV Botica
            (116, 7)  # YLV Grupo
        ]
        
        for subcat_id, company_id in subcats:
            print(f"\nMigrando subcategoría {subcat_id} (company_id={company_id})...")
            try:
                result = _migrate_to_final_internal(
                    company_id=company_id,
                    subcategoria_id=subcat_id,
                    allow_overwrite=True,
                    db=db
                )
                print(f"  Resultado: {result}")
            except Exception as e:
                print(f"  Error: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n=== VERIFICANDO RESULTADOS ===")
        from sqlalchemy import text
        result = db.execute(text("""
            SELECT subcategoria_id, estado, COUNT(*) as total
            FROM cf_diariol 
            WHERE subcategoria_id IN (80,81,82,83,116)
            GROUP BY subcategoria_id, estado
            ORDER BY subcategoria_id, estado
        """))
        
        for row in result:
            print(f"  Subcategoría {row[0]} | Estado '{row[1]}': {row[2]} registros")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_book_209()
