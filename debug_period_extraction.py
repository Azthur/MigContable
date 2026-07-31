#!/usr/bin/env python3
"""Script para debug de extracción de período."""
import sys
sys.path.insert(0, '/app')

from backend.app.core.database import get_dest_db
from backend.app.models.models import MapeoSubcategoria
from backend.app.api.endpoints.mapeo import _extract_period_month

def debug_period_extraction():
    db = next(get_dest_db())
    
    try:
        # Subcategoría 81 (YLV Nature, mes 07)
        sub = db.query(MapeoSubcategoria).filter(MapeoSubcategoria.id == 81).first()
        
        print(f"=== DEBUG SUBCATEGORÍA {sub.id}: {sub.nombre} ===")
        print(f"Filter rules: {sub.filter_rules}")
        print(f"Tabla origen: {sub.tabla_origen}")
        
        # Probar extracción de período
        periodo, mes = _extract_period_month(sub.filter_rules, None, sub=sub, df=None)
        
        print(f"\nResultado:")
        print(f"  Período: '{periodo}'")
        print(f"  Mes: '{mes}'")
        
        # Verificar si es None
        if periodo is None:
            print("  ⚠️ PERÍODO ES NONE - esto causa cper='nan'")
        else:
            print(f"  ✓ Período extraído correctamente")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_period_extraction()
