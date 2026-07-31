#!/usr/bin/env python3
"""Script para probar la generación de asientos del libro 209 con cper corregido."""
import sys
sys.path.insert(0, '/app')

from backend.app.core.database import get_dest_db
from backend.app.models.models import MapeoSubcategoria
from backend.app.api.endpoints.mapeo import generate_to_cf_diariol

def test_book_209_generation():
    db = next(get_dest_db())
    
    try:
        # Subcategorías del libro 209
        subcat_ids = [80, 81, 82, 83, 116]
        
        print("=== GENERANDO ASIENTOS DEL LIBRO 209 ===")
        
        for subcat_id in subcat_ids:
            print(f"\nGenerando para subcategoría {subcat_id}...")
            try:
                result = generate_to_cf_diariol(
                    {
                        "subcategoria_id": subcat_id,
                        "clear_previous": True,
                        "is_realtime": False
                    },
                    db
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
        
        print("\n=== VERIFICANDO VALORES cper ===")
        result = db.execute(text("""
            SELECT cper, COUNT(*) as total
            FROM cf_diariol 
            WHERE subcategoria_id IN (80,81,82,83,116)
            GROUP BY cper
            ORDER BY total DESC
        """))
        
        for row in result:
            print(f"  cper='{row[0]}': {row[1]} registros")
        
        print("\n=== VERIFICANDO VALORES cmes ===")
        result = db.execute(text("""
            SELECT cmes, COUNT(*) as total
            FROM cf_diariol 
            WHERE subcategoria_id IN (80,81,82,83,116)
            GROUP BY cmes
            ORDER BY total DESC
        """))
        
        for row in result:
            print(f"  cmes='{row[0]}': {row[1]} registros")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_book_209_generation()
