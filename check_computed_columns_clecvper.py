#!/usr/bin/env python3
"""Script para revisar reglas de columnas calculadas para clecvper y cledmcper."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def check_computed_columns_clecvper():
    db = next(get_dest_db())
    
    try:
        print("=== REGLAS DE COLUMNAS CALCULADAS PARA CLECVPER Y CLEDMPER ===")
        
        result = db.execute(text("""
            SELECT id, table_selection_id, column_name, rule_type, rule_expression
            FROM computed_column_rules
            WHERE column_name IN ('clecvper', 'cledmcper')
            ORDER BY table_selection_id, column_name
        """))
        
        for row in result:
            print(f"  ID {row[0]}: table_selection_id {row[1]} - {row[2]}")
            print(f"    Tipo: {row[3]} | Expresión: {row[4]}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_computed_columns_clecvper()
