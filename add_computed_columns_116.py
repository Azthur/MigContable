#!/usr/bin/env python3
"""Script para agregar reglas de columnas calculadas para subcategoría 116."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def add_computed_columns_116():
    db = next(get_dest_db())
    
    try:
        print("=== AGREGANDO REGLAS DE COLUMNAS CALCULADAS PARA SUBCATEGORÍA 116 ===")
        
        # Table selection ID para FinPlanillaMovilidadDet en company_id 7
        table_selection_id = 92
        
        # Primero eliminar reglas existentes para ccodcue si las hay
        db.execute(text("""
            DELETE FROM computed_column_rules
            WHERE table_selection_id = :ts_id
            AND new_column_name = 'ccodcue'
        """), {"ts_id": table_selection_id})
        
        # Agregar regla para ccodcue usando C_ctatotalF primero, luego C_ctabaseF
        # Similar a como funciona la subcategoría 81
        db.execute(text("""
            INSERT INTO computed_column_rules 
            (table_selection_id, new_column_name, source_column, condition_value, result_value, default_value, priority, is_active)
            VALUES 
            (:ts_id, 'ccodcue', 'C_ctatotalF', 'C_ctatotalF IS NOT NULL', 'C_ctatotalF', 'C_ctabaseF', 1, true)
        """), {"ts_id": table_selection_id})
        
        # Agregar segunda regla para usar C_ctabaseF si C_ctatotalF es null
        db.execute(text("""
            INSERT INTO computed_column_rules 
            (table_selection_id, new_column_name, source_column, condition_value, result_value, default_value, priority, is_active)
            VALUES 
            (:ts_id, 'ccodcue', 'C_ctabaseF', 'C_ctabaseF IS NOT NULL', 'C_ctabaseF', '469901', 2, true)
        """), {"ts_id": table_selection_id})
        
        db.commit()
        
        print("Reglas agregadas exitosamente")
        
        # Verificar las reglas agregadas
        result = db.execute(text("""
            SELECT new_column_name, source_column, condition_value, result_value, default_value, priority, is_active
            FROM computed_column_rules
            WHERE table_selection_id = :ts_id
            ORDER BY priority
        """), {"ts_id": table_selection_id})
        
        print("\nReglas actuales:")
        for row in result:
            print(f"  {row[0]} <- {row[1]}")
            print(f"    Condición: {row[2]}")
            print(f"    Resultado: {row[3]}")
            print(f"    Default: {row[4]}")
            print(f"    Prioridad: {row[5]} | Activo: {row[6]}")
            print()
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_computed_columns_116()
