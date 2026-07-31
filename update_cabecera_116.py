#!/usr/bin/env python3
"""Script para actualizar cuentas contables en tabla cabecera para company_id 7."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def update_cabecera_116():
    db = next(get_dest_db())
    
    try:
        print("=== ACTUALIZANDO CUENTAS CONTABLES EN TABLA CABECERA ===")
        
        # Usar las mismas cuentas que la subcategoría 81
        # C_Cuentabase: 6556179
        # C_Cuentatotal: 469901
        result = db.execute(text("""
            UPDATE FinPlanillaMovilidadCab
            SET "C_Cuentabase" = '6556179',
                "C_Cuentatotal" = '469901'
            WHERE company_id = 7
            AND ("C_Cuentabase" IS NULL OR "C_Cuentatotal" IS NULL)
        """))
        print(f"Registros actualizados: {result.rowcount}")
        
        db.commit()
        
        print("\nVerificando actualización...")
        result = db.execute(text("""
            SELECT "Id", "C_Cuentabase", "C_Cuentatotal"
            FROM FinPlanillaMovilidadCab
            WHERE company_id = 7
            LIMIT 5
        """))
        
        for row in result:
            print(f"  Id: {row[0]} | C_Cuentabase: {row[1]} | C_Cuentatotal: {row[2]}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_cabecera_116()
