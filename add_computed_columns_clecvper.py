#!/usr/bin/env python3
"""Script para agregar reglas de columnas calculadas para clecvper y cledmcper."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def add_computed_columns_clecvper():
    db = next(get_dest_db())
    
    try:
        print("=== AGREGANDO REGLAS DE COLUMNAS CALCULADAS PARA CLECVPER Y CLEDMPER ===")
        
        # Table selections para libro 209
        table_selections = [66, 70, 74, 92]  # FinPlanillaMovilidadDet para diferentes companies
        
        for ts_id in table_selections:
            print(f"\n--- Table Selection ID {ts_id} ---")
            
            # Verificar si ya existe regla para clecvper
            result = db.execute(text("""
                SELECT COUNT(*) FROM computed_column_rules
                WHERE table_selection_id = :ts_id AND new_column_name = 'clecvper'
            """), {"ts_id": ts_id})
            
            if result.scalar() == 0:
                # Agregar regla para clecvper
                result = db.execute(text("""
                    INSERT INTO computed_column_rules 
                    (table_selection_id, new_column_name, source_column, condition_value, result_value, default_value, priority, is_active)
                    VALUES (:ts_id, 'clecvper', 'cper', '', '', '', 10, True)
                """), {"ts_id": ts_id})
                print(f"  Regla clecvper agregada: {result.rowcount} filas")
            else:
                print(f"  Regla clecvper ya existe")
            
            # Verificar si ya existe regla para cledmcper
            result = db.execute(text("""
                SELECT COUNT(*) FROM computed_column_rules
                WHERE table_selection_id = :ts_id AND new_column_name = 'cledmcper'
            """), {"ts_id": ts_id})
            
            if result.scalar() == 0:
                # Agregar regla para cledmcper
                result = db.execute(text("""
                    INSERT INTO computed_column_rules 
                    (table_selection_id, new_column_name, source_column, condition_value, result_value, default_value, priority, is_active)
                    VALUES (:ts_id, 'cledmcper', 'cper', '', '', '', 11, True)
                """), {"ts_id": ts_id})
                print(f"  Regla cledmcper agregada: {result.rowcount} filas")
            else:
                print(f"  Regla cledmcper ya existe")
        
        db.commit()
        
        print("\n=== VERIFICANDO REGLAS AGREGADAS ===")
        result = db.execute(text("""
            SELECT table_selection_id, new_column_name, source_column
            FROM computed_column_rules
            WHERE new_column_name IN ('clecvper', 'cledmcper')
            AND table_selection_id IN (66, 70, 74, 92)
            ORDER BY table_selection_id, new_column_name
        """))
        
        for row in result:
            print(f"  table_selection_id {row[0]} - {row[1]}: source = {row[2]}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_computed_columns_clecvper()
