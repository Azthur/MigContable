#!/usr/bin/env python3
"""Script para revisar datos de origen detallados para company_id 7."""
import sys
sys.path.insert(0, '/app')

import logging
logging.disable(logging.CRITICAL)

from backend.app.core.database import get_dest_db
from sqlalchemy import text

def check_origen_116_detail():
    db = next(get_dest_db())
    
    try:
        print("=== DATOS DE ORIGEN DETALLADOS PARA COMPANY_ID 7 ===")
        
        result = db.execute(text("""
            SELECT "C_CodAux", "C_ctabaseF", "C_ctatotalF", idcontrol, "PlanillaId"
            FROM finplanillamovilidaddet
            WHERE company_id = 7
            LIMIT 10
        """))
        
        for row in result:
            print(f"  C_CodAux: {row[0]} | C_ctabaseF: {row[1]} | C_ctatotalF: {row[2]} | idcontrol: {row[3]} | PlanillaId: {row[4]}")
        
        # Revisar si hay valores en la tabla cabecera
        print("\n=== VERIFICANDO TABLA CABECERA PARA PLANILLAS ===")
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
    finally:
        db.close()

if __name__ == "__main__":
    check_origen_116_detail()
