#!/usr/bin/env python3
"""Script para regenerar registros de subcategoría 116 con nuevas reglas de ccodcue."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

import importlib
import backend.app.api.endpoints.mapeo as mapeo_module
importlib.reload(mapeo_module)

from backend.app.core.database import get_dest_db
from backend.app.api.endpoints.mapeo import delete_subcategoria_asientos
from sqlalchemy import text

def regenerate_subcat_116():
    db = next(get_dest_db())
    
    try:
        print("=== REGENERANDO REGISTROS DE SUBCATEGORÍA 116 ===")
        
        # Primero eliminar registros existentes
        print("\n1. Eliminando registros existentes...")
        result = db.execute(text("""
            DELETE FROM cf_diariol
            WHERE subcategoria_id = 116
        """))
        print(f"   Registros eliminados: {result.rowcount}")
        
        result = db.execute(text("""
            DELETE FROM cf_diario
            WHERE subcategoria_id = 116
        """))
        print(f"   Cabeceras eliminadas: {result.rowcount}")
        
        # Resetear control de generación
        db.execute(text("""
            UPDATE mapeo_subcategorias
            SET last_generated_control_value = NULL
            WHERE id = 116
        """))
        
        db.commit()
        
        print("\n2. Regenerando asientos...")
        # Obtener objeto de subcategoría
        from backend.app.models.models import MapeoSubcategoria
        sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == 116).first()
        
        if not sub:
            print("   ERROR: No se encontró subcategoría 116")
            return
        
        # Usar la función de generación interna
        from backend.app.api.endpoints.mapeo import _generate_subcategoria_cf_diariol
        result = _generate_subcategoria_cf_diariol(
            sub=sub,
            db=db,
            company_id=7
        )
        print(f"   Resultado: {result}")
        
        print("\n3. Verificando ccodcue en staging...")
        result = db.execute(text("""
            SELECT DISTINCT ccodcue, COUNT(*) as total
            FROM cf_diariol
            WHERE subcategoria_id = 116
            GROUP BY ccodcue
            ORDER BY ccodcue
        """))
        
        for row in result:
            print(f"   ccodcue: {row[0]} | Total: {row[1]}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    regenerate_subcat_116()
